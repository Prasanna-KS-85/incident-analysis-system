"""
CCED — Clustered Civil Emergency Detection Engine
==================================================
Scans recent grievance tickets, groups geographically and temporally
proximate incidents of the same category into clusters, computes an
Emergence-Boosted Cluster CCI, and upserts active clusters into the
`clusters` MongoDB collection.

Formula:
    Cluster_CCI = min(10.0, mean(member_ccis) + log2(N) * EMERGENCE_BONUS_FACTOR)
"""

import math
from datetime import datetime, timedelta

import pymongo
from bson.objectid import ObjectId

# ─── Project-internal DB connection ───────────────────────────────
from db_handler import DatabaseHandler

# ==================================================================
# CONSTANTS
# ==================================================================
RADIUS_METRES        = 500          # Max distance between two tickets to be "nearby"
TIME_WINDOW_HOURS    = 2            # Only consider tickets submitted in the last N hours
MIN_CLUSTER_SIZE     = 3            # Minimum tickets required to form a cluster
EMERGENCE_BONUS_FACTOR = 0.8       # Multiplier applied to log2(N) bonus

# ==================================================================
# SYSTEMIC EVENT LABEL MAPPING
# Maps DistilBERT classification categories → human-readable
# systemic-event descriptions surfaced when a cluster is detected.
# ==================================================================
SYSTEMIC_LABELS = {
    "Water Supply & Drainage":                "Possible Pipe Burst / Water Main Failure",
    "Fire & Disaster":                        "Possible Large Fire / Disaster Zone",
    "Electrical & Power Infrastructure":      "Possible Grid Failure / Mass Power Outage",
    "Roads & Transportation Infrastructure":  "Possible Road Collapse / Major Blockage",
    "Sanitation & Public Health":             "Possible Disease Outbreak / Sanitation Crisis",
    "Public Safety & Emergency":              "Possible Civil Unrest / Mass Safety Threat",
    "Medical & Health":                       "Possible Mass Casualty / Health Emergency",
}

# ==================================================================
# MATH HELPER — Haversine Formula
# ==================================================================
_EARTH_RADIUS_M = 6_371_000  # Earth's mean radius in metres

def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the great-circle distance between two points on Earth
    using the Haversine formula.

    Parameters
    ----------
    lat1, lon1 : float   — Coordinates of point A (decimal degrees)
    lat2, lon2 : float   — Coordinates of point B (decimal degrees)

    Returns
    -------
    float — Distance in **metres**.
    """
    # Convert decimal degrees → radians
    phi1    = math.radians(lat1)
    phi2    = math.radians(lat2)
    d_phi   = math.radians(lat2 - lat1)
    d_lambda = math.radians(lon2 - lon1)

    a = (math.sin(d_phi / 2) ** 2
         + math.cos(phi1) * math.cos(phi2)
         * math.sin(d_lambda / 2) ** 2)

    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return _EARTH_RADIUS_M * c


# ==================================================================
# HELPER — Extract lat/lon from a ticket document
# Handles both flat keys (batch uploads) and nested GPS dict (portal)
# ==================================================================
def _extract_coords(ticket: dict) -> tuple:
    """Return (lat, lon) for a ticket, or (None, None) if unavailable."""
    # Flat keys (batch JSON)
    lat = ticket.get("lat")
    lon = ticket.get("lon")
    if lat is not None and lon is not None:
        try:
            return float(lat), float(lon)
        except (ValueError, TypeError):
            pass

    # Nested GPS dict (citizen portal)
    gps = ticket.get("gps")
    if isinstance(gps, dict):
        try:
            return float(gps["lat"]), float(gps["lon"])
        except (KeyError, ValueError, TypeError):
            pass

    return None, None


# ==================================================================
# CORE — Cluster Scanner
# ==================================================================
def scan_and_update(db_connection: DatabaseHandler) -> list:
    """
    Scan recent grievances, detect spatial-temporal clusters of the
    same category, compute Emergence-Boosted CCI, and upsert results
    into the ``clusters`` collection.

    Parameters
    ----------
    db_connection : DatabaseHandler
        An already-initialised DatabaseHandler instance whose
        ``.db`` attribute exposes the MongoDB database.

    Returns
    -------
    list[dict] — The cluster documents that were upserted (for logging
                 or downstream consumption).
    """
    if not db_connection.is_connected:
        print("⚠️  CCED: Database offline — skipping cluster scan.")
        return []

    db = db_connection.db  # pymongo Database object
    grievances_col = db_connection.collection
    clusters_col   = db["clusters"]

    # ── 1. QUERY recent, active tickets ───────────────────────────
    cutoff = datetime.utcnow() - timedelta(hours=TIME_WINDOW_HOURS)

    query = {
        "status": {"$in": ["Pending", "In Progress"]},
        "$or": [
            {"server_timestamp": {"$gte": cutoff}},
            {"timestamp":        {"$gte": cutoff.isoformat()}},
        ],
    }

    tickets = list(grievances_col.find(query))

    if not tickets:
        print("ℹ️  CCED: No recent active tickets found.")
        return []

    print(f"🔍 CCED: Scanning {len(tickets)} tickets for clusters...")

    # ── 2. GROUP tickets by category ──────────────────────────────
    by_category: dict[str, list] = {}
    for t in tickets:
        cat = t.get("category", "Unclassified")
        lat, lon = _extract_coords(t)
        if lat is None or lon is None:
            continue  # Skip tickets without valid coordinates
        entry = {
            "_id":  t["_id"],
            "lat":  lat,
            "lon":  lon,
            "cci":  float(t.get("cci", 0.0)),
            "text": t.get("translated_text", t.get("original_text", t.get("text", ""))),
        }
        by_category.setdefault(cat, []).append(entry)

    # ── 3. DETECT clusters within each category ───────────────────
    detected_clusters: list[dict] = []

    for category, members in by_category.items():
        # Simple single-pass greedy clustering:
        #   For each un-assigned ticket, start a new cluster seed.
        #   Pull in every other un-assigned ticket of the same
        #   category that is within RADIUS_METRES of the seed.
        assigned: set = set()

        for i, seed in enumerate(members):
            if seed["_id"] in assigned:
                continue

            group = [seed]
            assigned.add(seed["_id"])

            for j, candidate in enumerate(members):
                if candidate["_id"] in assigned:
                    continue
                dist = haversine(seed["lat"], seed["lon"],
                                 candidate["lat"], candidate["lon"])
                if dist <= RADIUS_METRES:
                    group.append(candidate)
                    assigned.add(candidate["_id"])

            # Only promote to cluster if threshold met
            if len(group) >= MIN_CLUSTER_SIZE:
                n = len(group)

                # Centroid
                centroid_lat = sum(m["lat"] for m in group) / n
                centroid_lon = sum(m["lon"] for m in group) / n

                # Emergence-Boosted CCI
                mean_cci    = sum(m["cci"] for m in group) / n
                cluster_cci = min(10.0,
                                  mean_cci + math.log2(n) * EMERGENCE_BONUS_FACTOR)

                # Systemic label
                systemic_label = SYSTEMIC_LABELS.get(
                    category, f"Multiple {category} Incidents Detected"
                )

                cluster_doc = {
                    "category":              category,
                    "member_ids":            [m["_id"] for m in group],
                    "member_count":          n,
                    "centroid": {
                        "lat": round(centroid_lat, 6),
                        "lon": round(centroid_lon, 6),
                    },
                    "cluster_cci":           round(cluster_cci, 2),
                    "systemic_event_label":  systemic_label,
                    "status":                "Active",
                    "detected_at":           datetime.utcnow(),
                    "window_hours":          TIME_WINDOW_HOURS,
                    "radius_metres":         RADIUS_METRES,
                }

                detected_clusters.append(cluster_doc)

    # ── 4. UPSERT into `clusters` collection ─────────────────────
    upserted: list[dict] = []

    for doc in detected_clusters:
        # Use (category + sorted member_ids) as a unique fingerprint
        # so re-running the scan updates existing clusters rather
        # than creating duplicates.
        sorted_ids = sorted(str(mid) for mid in doc["member_ids"])
        fingerprint = f"{doc['category']}::{'|'.join(sorted_ids)}"

        result = clusters_col.update_one(
            {"_fingerprint": fingerprint},
            {"$set": {**doc, "_fingerprint": fingerprint}},
            upsert=True,
        )

        action = "INSERTED" if result.upserted_id else "UPDATED"
        print(f"   ✅ {action} cluster: {doc['systemic_event_label']} "
              f"({doc['member_count']} tickets, CCI={doc['cluster_cci']})")

        upserted.append(doc)

    if not upserted:
        print("ℹ️  CCED: No clusters detected in current window.")

    return upserted


# ==================================================================
# STANDALONE EXECUTION (for manual testing)
# ==================================================================
if __name__ == "__main__":
    print("🚀 CCED Manual Scan")
    print("=" * 50)
    db = DatabaseHandler()
    clusters = scan_and_update(db)
    print(f"\n📊 Total clusters detected: {len(clusters)}")
    for c in clusters:
        print(f"   • {c['systemic_event_label']} | "
              f"CCI={c['cluster_cci']} | "
              f"Members={c['member_count']} | "
              f"Centroid=({c['centroid']['lat']}, {c['centroid']['lon']})")

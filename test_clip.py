import time
import torch
from PIL import Image
from transformers import CLIPProcessor, CLIPModel

def test_system_capability():
    print("1. INITIALIZING AI BRAIN (Downloading Model)...")
    print("   (This might take 1-2 minutes the first time)")
    
    try:
        # Load the model (We use 'openai/clip-vit-base-patch32' - precise but not too heavy)
        model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
        processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
        print("   ✅ Model Loaded Successfully!")
    except Exception as e:
        print(f"   ❌ Model Load Failed: {e}")
        return

    # Create a dummy image (Red Square) to simulate a "Fire"
    print("\n2. GENERATING TEST IMAGE...")
    image = Image.new('RGB', (200, 200), color = 'red')
    
    # The text labels we want the AI to check against
    labels = ["a photo of a fire", "a photo of a swimming pool", "a photo of a snowy mountain"]
    print(f"   Labels to check: {labels}")

    print("\n3. RUNNING INFERENCE (The Speed Test)...")
    start_time = time.time()
    
    # Process inputs
    inputs = processor(text=labels, images=image, return_tensors="pt", padding=True)
    
    # The AI "Thinking" part
    outputs = model(**inputs)
    logits_per_image = outputs.logits_per_image  # this is the image-text similarity score
    probs = logits_per_image.softmax(dim=1)  # we can take the softmax to get the label probabilities
    
    end_time = time.time()
    duration = end_time - start_time
    
    # Show results
    print(f"\n   ⏱️  AI Thinking Time: {duration:.4f} seconds")
    print("\n4. AI VERDICT:")
    for i, label in enumerate(labels):
        print(f"   - {label}: {probs[0][i].item()*100:.2f}% Match")

    # Final Hardware Verdict
    print("\n------------------------------------------------")
    if duration < 2.0:
        print("🚀 RESULT: EXCELLENT! Your laptop handles AI instantly.")
        print("   -> We can implement Real-Time Image Verification.")
    elif duration < 6.0:
        print("✅ RESULT: GOOD. It works, but maybe 2-3 sec delay.")
        print("   -> We will add a 'Processing...' spinner in the UI.")
    else:
        print("⚠️ RESULT: SLOW. It takes >6 seconds.")
        print("   -> We might need a lighter model or use Cloud API.")
    print("------------------------------------------------")

if __name__ == "__main__":
    test_system_capability()
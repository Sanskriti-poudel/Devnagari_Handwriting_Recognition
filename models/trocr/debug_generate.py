"""
Local CPU debug for the 0%-accuracy TrOCR checkpoint.

Loads the fine-tuned weights + base processor and inspects:
  1. tokenizer round-trip on Devanagari glyphs (does "क" -> ids -> "क"?)
  2. what the model actually generates vs ground truth on a few test images.

Run:
    python models/trocr/debug_generate.py --checkpoint <dir> [--n 8]
"""
import os, sys, argparse
import torch

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(THIS_DIR, "..", ".."))
sys.path.insert(0, THIS_DIR)
sys.path.insert(0, PROJECT_ROOT)

from transformers import TrOCRProcessor, VisionEncoderDecoderModel
from dataset import TrOCRDataset

BASE = os.environ.get("TROCR_MODEL", "microsoft/trocr-base-handwritten")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--checkpoint", required=True)
    ap.add_argument("--n", type=int, default=8)
    args = ap.parse_args()

    print(f"[debug] loading processor from base {BASE}")
    processor = TrOCRProcessor.from_pretrained(BASE)
    tok = processor.tokenizer

    # --- 1. tokenizer round-trip on glyphs ---
    print("\n=== tokenizer round-trip ===")
    for g in ["क", "ख", "थ", "१", "ज्ञ"]:
        ids = tok(g, add_special_tokens=False).input_ids
        back = tok.decode(ids, skip_special_tokens=True)
        print(f"  {g!r:8} -> ids={ids} -> {back!r}  {'OK' if back == g else 'MISMATCH'}")
    print(f"  cls={tok.cls_token_id} sep={tok.sep_token_id} pad={tok.pad_token_id} "
          f"bos={tok.bos_token_id} eos={tok.eos_token_id}")

    # --- 2. generation on real test images ---
    print(f"\n[debug] loading model from {args.checkpoint}")
    model = VisionEncoderDecoderModel.from_pretrained(args.checkpoint)
    model.eval()
    print(f"[debug] gen_config: decoder_start={model.generation_config.decoder_start_token_id} "
          f"eos={model.generation_config.eos_token_id} max_len={model.generation_config.max_length}")

    device = "cuda" if torch.cuda.is_available() else "cpu"
    model.to(device)
    ds = TrOCRDataset("test", processor, augment=None)

    # show a few raw generations to see exactly what comes out
    print(f"\n=== sample generations (first {min(args.n, 6)}) ===")
    with torch.no_grad():
        for i in range(min(args.n, 6)):
            item = ds[i]
            pv = item["pixel_values"].unsqueeze(0).to(device)
            gt = tok.decode(item["labels"].tolist(), skip_special_tokens=True).strip()
            gen = model.generate(pv, max_length=8)
            print(f"  [{i}] gt={gt!r} gt_ids={item['labels'].tolist()}")
            print(f"      pred={tok.decode(gen[0], skip_special_tokens=True).strip()!r} "
                  f"pred_ids={gen[0].tolist()}")

    # compare generation strategies on N samples — does forcing tokens / beams fix it?
    strategies = {
        "greedy (max_len=8)":        dict(max_length=8),
        "greedy min2 (min/max new)": dict(min_new_tokens=2, max_new_tokens=6),
        "beam4 min2":                dict(num_beams=4, min_new_tokens=2, max_new_tokens=6),
    }
    print(f"\n=== accuracy over {args.n} samples by strategy ===")
    with torch.no_grad():
        for name, kw in strategies.items():
            correct = 0
            for i in range(args.n):
                item = ds[i]
                pv = item["pixel_values"].unsqueeze(0).to(device)
                gt = tok.decode(item["labels"].tolist(), skip_special_tokens=True).strip()
                gen = model.generate(pv, **kw)
                pred = tok.decode(gen[0], skip_special_tokens=True).strip()
                correct += int(pred == gt)
            print(f"  {name:28} : {correct}/{args.n} = {correct/args.n*100:.1f}%")


if __name__ == "__main__":
    main()

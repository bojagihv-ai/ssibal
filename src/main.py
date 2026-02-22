from __future__ import annotations

import argparse
import json

from src.core.pipeline import run_pipeline


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="sachyo")
    sub = p.add_subparsers(dest="command", required=True)

    run = sub.add_parser("run", help="run end-to-end pipeline")
    run.add_argument("--image", required=True)
    run.add_argument("--query_hint", default="")
    run.add_argument("--max_candidates_per_source", type=int, default=30)
    run.add_argument("--topk_final", type=int, default=50)
    run.add_argument(
        "--sources",
        default="coupang,naver,11st,gmarket,auction,ssg,lotteon,wemakeprice,tmon,interpark",
    )
    run.add_argument("--output_dir", default="./output")
    run.add_argument("--export_xlsx", action="store_true")
    run.add_argument("--manual_review_topn", type=int, default=30)
    return p


def main() -> None:
    args = build_parser().parse_args()
    if args.command == "run":
        result = run_pipeline(
            image_path=args.image,
            query_hint=args.query_hint,
            max_candidates_per_source=args.max_candidates_per_source,
            topk_final=args.topk_final,
            sources=[s.strip() for s in args.sources.split(",") if s.strip()],
            output_base_dir=args.output_dir,
            export_xlsx=args.export_xlsx,
            manual_review_topn=args.manual_review_topn,
        )
        print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

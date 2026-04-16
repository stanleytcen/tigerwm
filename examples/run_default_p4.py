from argparse import ArgumentParser

from tigerwm import tigerwm


def build_parser():
    parser = ArgumentParser(description="Run tigerwm default P4 pipeline.")
    parser.add_argument("--dwi", required=True, help="Path to 4D DWI NIfTI.")
    parser.add_argument("--bvals", required=True, help="Path to bvals file.")
    parser.add_argument("--bvecs", required=True, help="Path to bvecs file.")
    parser.add_argument("--out-dir", required=True, help="Output directory.")
    parser.add_argument("--templates-dir", required=True, help="Directory containing JHU templates.")
    parser.add_argument("--subject", default=None, help="Subject ID written to CSV.")
    parser.add_argument("--csv-path", default=None, help="Optional CSV output path.")
    parser.add_argument("--force", action="store_true", help="Overwrite existing outputs.")
    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()
    if args.csv_path and not args.subject:
        parser.error("--subject is required when --csv-path is provided")
    res = tigerwm(
        args.dwi,
        args.bvals,
        args.bvecs,
        args.out_dir,
        templates_dir=args.templates_dir,
        subject=args.subject,
        csv_path=args.csv_path,
        force=args.force,
    )
    print("pipeline:", res["pipeline"])
    print("steps:", res["steps"])
    print("final dwi:", res["dwi"])
    print("roi keys:", len(res.get("roi", {})))


if __name__ == "__main__":
    main()


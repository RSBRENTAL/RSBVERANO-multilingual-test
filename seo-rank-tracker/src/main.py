import argparse
from .connectors import google_search_console, bing_webmaster, google_ai_import
from .reports.export_csv import export as export_csv
from .reports.export_html import export as export_html

def run_google(args):
    rows = google_search_console.run(dry_run=args.dry_run, period=args.period, start_date=args.start_date, end_date=args.end_date)
    export_csv(rows, "reports/google-search-console.csv")
    return rows

def run_bing(args):
    rows = bing_webmaster.run(dry_run=args.dry_run)
    export_csv(rows, "reports/bing-webmaster.csv")
    return rows

def run_import_google_ai(args):
    rows = google_ai_import.run(dry_run=args.dry_run)
    export_csv(rows, "reports/google-generative-ai.csv")
    return rows

def run_report(rows=None):
    rows = rows or []
    export_csv(rows, "reports/latest-report.csv")
    export_html(rows, "reports/latest-report.html")
    return rows

def build_parser():
    parser = argparse.ArgumentParser(description="Independent SEO rank tracker")
    parser.add_argument("command", choices=["google","bing","import-google-ai","report","all"])
    parser.add_argument("--dry-run", action="store_true", help="Do not perform external connections")
    parser.add_argument("--period", default="7d", choices=["7d","28d","3m","custom"])
    parser.add_argument("--start-date", default="")
    parser.add_argument("--end-date", default="")
    return parser

def main(argv=None):
    args = build_parser().parse_args(argv)
    rows=[]
    if args.command == "google": rows = run_google(args)
    elif args.command == "bing": rows = run_bing(args)
    elif args.command == "import-google-ai": rows = run_import_google_ai(args)
    elif args.command == "report": rows = run_report([])
    elif args.command == "all":
        rows.extend(run_google(args)); rows.extend(run_bing(args)); rows.extend(run_import_google_ai(args)); run_report(rows)
    print(f"Rows: {len(rows)}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())

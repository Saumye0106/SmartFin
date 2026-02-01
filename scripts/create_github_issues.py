#!/usr/bin/env python3
"""
Create GitHub issues from `backlog/Product Backlog.csv`.

Usage:
  export GITHUB_TOKEN=ghp_xxx    # or set in Windows env
  python scripts/create_github_issues.py --repo youruser/smartfin

The script will create an issue per row. For items with Priority 'Must',
an acceptance checklist will be added to the issue body.
"""
import os
import csv
import argparse
import requests

GITHUB_API = 'https://api.github.com'


def read_backlog(path):
    rows = []
    with open(path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for r in reader:
            rows.append(r)
    return rows


def make_issue_body(row):
    lines = []
    lines.append(row.get('User Story', '').strip())
    lines.append('')
    ac = row.get('Acceptance Criteria', '').strip()
    if ac:
        lines.append('**Acceptance Criteria**')
        lines.append(ac)
        lines.append('')

    fr = row.get('Functional Requirements', '').strip()
    if fr:
        lines.append('**Functional Requirements**')
        lines.append(fr)
        lines.append('')

    nfr = row.get('Non-Functional Requirements', '').strip()
    if nfr:
        lines.append('**Non-Functional Requirements**')
        lines.append(nfr)
        lines.append('')

    # Add acceptance-test checklist for Must items
    priority = row.get('Priority (MoSCoW)', '').strip().lower()
    if priority == 'must':
        lines.append('**Acceptance Tests**')
        # Parse acceptance criteria lines if tab/line separated
        ac_lines = [ln.strip() for ln in ac.splitlines() if ln.strip()]
        for ln in ac_lines:
            lines.append(f'- [ ] {ln}')
        lines.append('')

    return '\n'.join(lines)


def create_issue(repo, token, title, body, labels=None):
    url = f'{GITHUB_API}/repos/{repo}/issues'
    headers = {'Authorization': f'token {token}'}
    payload = {'title': title, 'body': body}
    if labels:
        payload['labels'] = labels
    resp = requests.post(url, json=payload, headers=headers)
    if resp.status_code == 201:
        print('Created:', resp.json().get('html_url'))
    else:
        print('Failed to create issue:', resp.status_code, resp.text)


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--repo', required=True, help='owner/repo')
    p.add_argument('--backlog', default='backlog/Product Backlog.csv')
    p.add_argument('--dry-run', action='store_true', help='Print issue payloads instead of posting')
    args = p.parse_args()
    args = p.parse_args()

    # In dry-run mode we don't need a token
    token = os.environ.get('GITHUB_TOKEN')
    if not args.dry_run and not token:
        raise SystemExit('Set GITHUB_TOKEN environment variable (or use --dry-run)')

    rows = read_backlog(args.backlog)
    for r in rows:
        title = f"[{r.get('Priority (MoSCoW)', '').strip()}] {r.get('Title','').strip()}"
        body = make_issue_body(r)
        labels = [r.get('Epic','').strip()] if r.get('Epic') else None
        if args.dry_run:
            # Print a compact preview of the issue payload
            print('---')
            print('Title:', title)
            print('Labels:', labels)
            print('Body Preview:')
            for line in body.splitlines()[:12]:
                print('  ', line)
            if len(body.splitlines()) > 12:
                print('  ... (truncated)')
            print('---')
        else:
            create_issue(args.repo, token, title, body, labels)


if __name__ == '__main__':
    main()

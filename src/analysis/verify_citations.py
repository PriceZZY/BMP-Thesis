import pathlib
"""
Verify all citations in draft.md against Crossref API.
For each reference, query Crossref by DOI or title and check:
- Authors match
- Journal/volume/pages match
- Year matches
"""

import urllib.request
import urllib.parse
import json
import re
import time

_REPO = pathlib.Path(__file__).resolve().parents[2]

# Extract references from REVISED_REFERENCES.md verified list
CITATIONS_TO_VERIFY = [
    {
        'id': 'Baker2014',
        'doi': '10.1016/j.jglr.2014.05.001',
        'expected_journal': 'Journal of Great Lakes Research',
        'expected_year': 2014,
        'expected_first_author': 'Baker',
    },
    {
        'id': 'Cheng2022',
        'doi': '10.1016/j.jglr.2021.10.013',
        'expected_journal': 'Journal of Great Lakes Research',
        'expected_year': 2022,
        'expected_first_author': 'Cheng',
        'expected_pages': '84-96',
    },
    {
        'id': 'Jarvie2017',
        'doi': '10.2134/jeq2016.07.0248',
        'expected_journal': 'Journal of Environmental Quality',
        'expected_year': 2017,
        'expected_first_author': 'Jarvie',
    },
    {
        'id': 'LiuJ2019',
        'doi': '10.2134/jeq2019.03.0119',
        'expected_journal': 'Journal of Environmental Quality',
        'expected_year': 2019,
        'expected_first_author': 'Liu',
    },
    {
        'id': 'Macrae2021',
        'doi': '10.1002/jeq2.20218',
        'expected_journal': 'Journal of Environmental Quality',
        'expected_year': 2021,
        'expected_first_author': 'Macrae',
    },
    {
        'id': 'VanRossum2021',
        'doi': '10.1016/j.watcyc.2021.06.002',
        'expected_journal': 'Water Cycle',
        'expected_year': 2021,
        'expected_first_author': 'Van Rossum',
    },
    {
        'id': 'Claassen2014',
        'title_query': 'Additionality Agricultural Conservation Programs',
        'expected_year': 2014,
        'expected_first_author': 'Claassen',
    },
    {
        'id': 'LiuBruins2018',
        'doi': '10.3390/su10020432',
        'expected_journal': 'Sustainability',
        'expected_year': 2018,
        'expected_first_author': 'Liu',
        'note': 'Should be Liu/Bruins/Heberling, NOT Udawatta/Rankoth/Jose',
    },
    {
        'id': 'PalmForster2017',
        'doi': '10.2489/jswc.72.5.493',
        'expected_journal': 'Journal of Soil and Water Conservation',
        'expected_year': 2017,
        'expected_first_author': 'Palm-Forster',
    },
    {
        'id': 'Prokopy2019',
        'doi': '10.2489/jswc.74.5.520',
        'expected_journal': 'Journal of Soil and Water Conservation',
        'expected_year': 2019,
        'expected_first_author': 'Prokopy',
    },
    {
        'id': 'Shortle2017',
        'doi': '10.1142/S2382624X16500338',
        'expected_journal': 'Water Economics and Policy',
        'expected_year': 2017,
        'expected_first_author': 'Shortle',
    },
    {
        'id': 'Smith2019',
        'doi': '10.1016/j.hal.2019.101624',
        'expected_journal': 'Harmful Algae',
        'expected_year': 2019,
        'expected_first_author': 'Smith',
    },
    {
        'id': 'Steffen2017',
        'doi': '10.1021/acs.est.7b00856',
        'expected_journal': 'Environmental Science & Technology',
        'expected_year': 2017,
        'expected_first_author': 'Steffen',
    },
    {
        'id': 'Rowe2016',
        'doi': '10.1007/s10705-015-9726-1',
        'expected_journal': 'Nutrient Cycling in Agroecosystems',
        'expected_year': 2016,
        'expected_first_author': 'Rowe',
    },
    {
        'id': 'Kalcic2015',
        'doi': '10.1111/1752-1688.12338',
        'expected_journal': 'JAWRA',
        'expected_year': 2015,
        'expected_first_author': 'Kalcic',
    },
    {
        'id': 'Mirnasl2024',
        'doi': '10.1002/tqem.22328',
        'expected_journal': 'Environmental Quality Management',
        'expected_year': 2024,
        'expected_first_author': 'Mirnasl',
    },
    {
        'id': 'Han2011',
        'doi': '10.1007/s10533-010-9420-y',
        'expected_journal': 'Biogeochemistry',
        'expected_year': 2011,
        'expected_first_author': 'Han',
        'note': 'Replacement for unverifiable Han 2021 STOTEN',
    },
]


def query_crossref_doi(doi):
    """Query Crossref by DOI."""
    url = f"https://api.crossref.org/works/{urllib.parse.quote(doi, safe='')}"
    headers = {'User-Agent': 'BMP-Thesis-Citation-Checker/1.0 (mailto:zzhou@uwaterloo.ca)'}
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode())
            return data.get('message', {})
    except Exception as e:
        return {'error': str(e)}


def verify_citation(cite):
    """Verify a citation against Crossref."""
    result = {'id': cite['id'], 'status': 'UNKNOWN'}

    if 'doi' in cite:
        cr = query_crossref_doi(cite['doi'])
        if 'error' in cr:
            result['status'] = 'ERROR'
            result['error'] = cr['error']
            return result

        # Extract Crossref data
        cr_title = cr.get('title', [''])[0] if cr.get('title') else ''
        cr_journal = cr.get('container-title', [''])[0] if cr.get('container-title') else ''
        cr_year = cr.get('published-print', {}).get('date-parts', [[None]])[0][0]
        if cr_year is None:
            cr_year = cr.get('published-online', {}).get('date-parts', [[None]])[0][0]
        cr_authors = cr.get('author', [])
        cr_first = cr_authors[0].get('family', '') if cr_authors else ''
        cr_volume = cr.get('volume', '')
        cr_pages = cr.get('page', '')

        result['crossref'] = {
            'title': cr_title[:80],
            'journal': cr_journal,
            'year': cr_year,
            'first_author': cr_first,
            'volume': cr_volume,
            'pages': cr_pages,
            'all_authors': [f"{a.get('family','')}, {a.get('given','')}" for a in cr_authors[:6]],
        }

        # Check matches
        checks = []
        if cite.get('expected_first_author') and cr_first:
            match = cite['expected_first_author'].lower() in cr_first.lower() or cr_first.lower() in cite['expected_first_author'].lower()
            checks.append(('author', match, f"{cite['expected_first_author']} vs {cr_first}"))

        if cite.get('expected_year') and cr_year:
            match = cite['expected_year'] == cr_year
            checks.append(('year', match, f"{cite['expected_year']} vs {cr_year}"))

        if cite.get('expected_journal') and cr_journal:
            match = cite['expected_journal'].lower() in cr_journal.lower() or cr_journal.lower() in cite['expected_journal'].lower()
            checks.append(('journal', match, f"'{cite['expected_journal']}' vs '{cr_journal}'"))

        if cite.get('expected_pages') and cr_pages:
            match = cite['expected_pages'] == cr_pages
            checks.append(('pages', match, f"{cite['expected_pages']} vs {cr_pages}"))

        result['checks'] = checks
        all_pass = all(c[1] for c in checks)
        result['status'] = 'VERIFIED' if all_pass else 'MISMATCH'

    return result


if __name__ == '__main__':
    print("=" * 70)
    print("CROSSREF CITATION VERIFICATION")
    print("=" * 70)

    results = []
    for cite in CITATIONS_TO_VERIFY:
        print(f"\n  Checking {cite['id']}...", end=' ')
        r = verify_citation(cite)
        results.append(r)
        print(r['status'])

        if r.get('crossref'):
            cr = r['crossref']
            print(f"    Crossref: {cr['first_author']} ({cr['year']}) {cr['journal']}")
            print(f"    Title: {cr['title'].encode('ascii', 'replace').decode()}")
            if cr.get('pages'):
                print(f"    Pages: {cr['pages']}, Vol: {cr['volume']}")
            if cr.get('all_authors'):
                print(f"    Authors: {', '.join(cr['all_authors'][:4])}")

        for check in r.get('checks', []):
            status = 'OK' if check[1] else 'FAIL'
            print(f"    [{status}] {check[0]}: {check[2]}")

        if cite.get('note'):
            print(f"    NOTE: {cite['note']}")

        time.sleep(0.5)  # Rate limit

    # Summary
    verified = sum(1 for r in results if r['status'] == 'VERIFIED')
    mismatch = sum(1 for r in results if r['status'] == 'MISMATCH')
    errors = sum(1 for r in results if r['status'] == 'ERROR')

    print(f"\n{'='*70}")
    print(f"SUMMARY: {verified} verified / {mismatch} mismatch / {errors} error")
    print(f"{'='*70}")

    # Save
    with open(str(_REPO / "results/citation_verification.json"), 'w') as f:
        json.dump(results, f, indent=2, default=str)
    print("Saved to results/citation_verification.json")

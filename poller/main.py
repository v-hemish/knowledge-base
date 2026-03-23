from yagooglesearch import SearchClient

QUERY = (
    '("site reliability engineer" OR sre OR devops OR "platform engineer" OR "production engineer") '
    '(site:jobs.lever.co OR site:boards.greenhouse.io OR site:job-boards.greenhouse.io)'
)

def main():
    client = SearchClient(
        query=QUERY,
        max_search_result_urls_to_return=30,
        http_429_cool_off_time_in_minutes=60,
        http_429_cool_off_factor=1.5,
        verbosity=2,
    )

    urls = client.search()
    print(f"Found {len(urls)} results\n")

    for i, url in enumerate(urls, 1):
        print(f"{i}. {url}")

if __name__ == "__main__":
    main()
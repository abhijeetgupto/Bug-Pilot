import optparse
import requests
import re
from bs4 import BeautifulSoup

# https://adsonair.withgoogle.com/
# https://app-cdn.clickup.com/main.8782c100b2160085.js


_regex = {
    'google_api': r'AIza[0-9A-Za-z-_]{35}',
    'google_captcha': r'6L[0-9A-Za-z-_]{38}|^6[0-9a-zA-Z_-]{39}$',
    'google_oauth': r'ya29\.[0-9A-Za-z\-_]+',
    'amazon_aws_access_key_id': r'A[SK]IA[0-9A-Z]{16}',
    'amazon_mws_auth_toke': r'amzn\\.mws\\.[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}',
    'amazon_aws_url': r's3\.amazonaws.com[/]+|[a-zA-Z0-9_-]*\.s3\.amazonaws.com',
    'facebook_access_token': r'EAACEdEose0cBA[0-9A-Za-z]+',
    'authorization_basic': r'basic\s*[a-zA-Z0-9=:_\+\/-]+',
    'authorization_bearer': r'bearer\s*[a-zA-Z0-9_\-\.=:_\+\/]+',
    'authorization_api': r'api[key|\s*]+[a-zA-Z0-9_\-]+',
    'mailgun_api_key': r'key-[0-9a-zA-Z]{32}',
    'twilio_api_key': r'SK[0-9a-fA-F]{32}',
    'twilio_account_sid': r'AC[a-zA-Z0-9_\-]{32}',
    'twilio_app_sid': r'AP[a-zA-Z0-9_\-]{32}',
    'paypal_braintree_access_token': r'access_token\$production\$[0-9a-z]{16}\$[0-9a-f]{32}',
    'square_oauth_secret': r'sq0csp-[ 0-9A-Za-z\-_]{43}|sq0[a-z]{3}-[0-9A-Za-z\-_]{22,43}',
    'square_access_token': r'sqOatp-[0-9A-Za-z\-_]{22}|EAAA[a-zA-Z0-9]{60}',
    'stripe_standard_api': r'sk_live_[0-9a-zA-Z]{24}',
    'stripe_restricted_api': r'rk_live_[0-9a-zA-Z]{24}',
    'github_access_token': r'[a-zA-Z0-9_-]*:[a-zA-Z0-9_\-]+@github\.com*',
    'rsa_private_key': r'-----BEGIN RSA PRIVATE KEY-----',
    'ssh_dsa_private_key': r'-----BEGIN DSA PRIVATE KEY-----',
    'ssh_dc_private_key': r'-----BEGIN EC PRIVATE KEY-----',
    'pgp_private_block': r'-----BEGIN PGP PRIVATE KEY BLOCK-----',
    'json_web_token': r'ey[A-Za-z0-9-_=]+\.[A-Za-z0-9-_=]+\.?[A-Za-z0-9-_.+/=]*$',
}



def find_secret(html, leaks_found):
    temp = []
    for api_regex in _regex:
        leaks = re.findall(_regex[api_regex], html)
        for leak in leaks:
            if api_regex in leaks_found:
                leaks_found[api_regex].append(leak)
            else:
                leaks_found[api_regex] = [leak]

    return


def find_link_in_webpage(base_url, url):
    base = base_url.replace("https://", "")
    content = requests.get(url)
    soup = BeautifulSoup(content.text, "html.parser")
    sources = soup.findAll('script', {"src": True})
    links = set()
    for source in sources:
        link = source['src']
        if "www" in link:
            if base in link:
                links.add(link)
            else:
                third_party_links.add(link)

        else:
            if base_url[-1] == "/":
                links.add(base_url + link[1:])
            else:
                links.add(base_url + link)

    return links


def get_all_links(base_url, depth):
    all_links = set()
    last = {base_url}

    for _ in range(depth):
        new = set()
        for url in last:
            links = find_link_in_webpage(base_url, url)
            for link in links:
                new.add(link)
            all_links.add(url)
        last = new
    for link in last:
        all_links.add(link)
    return all_links


third_party_links = set()


def find_vulnerabilities(base_url, depth=1):
    leaks_found = {}
    all_links_recursive = {}
    base_url = base_url
    all_links_recursive = get_all_links(base_url, depth)

    for link in all_links_recursive:
        print(link)

    if third_party_links:
        print("\nThird party links")
        for link in third_party_links:
            print(link)

    for link in all_links_recursive:
        html_content = requests.get(link).text
        find_secret(html_content, leaks_found)

    for api in leaks_found:
        print(f"\n {api}")
        for api_leaks in leaks_found[api]:
            print(api_leaks)

    return {
        "all_links_recursive": all_links_recursive,
        "third_party_links": third_party_links,
        "leaks_found": leaks_found
    }

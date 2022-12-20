from zipfile import ZipFile

from django.shortcuts import render, redirect
import os
import re

from api_key_checker.bug_pilot import find_vulnerabilities

import requests
import shutil
import chardet

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



def search_dir(dir_path, regex, api_key_name, output):
    pattern = re.compile(regex)  

    for root, dirs, files in os.walk(dir_path):
        for file in files:
            file_path = os.path.join(root, file)
            try:
                with open(file_path, encoding=encoding) as f:
                    for i, line in enumerate(f):
                        if pattern.search(line):
                            file_path = file_path.replace("folder/", "")
                            output.append({
                                "file_path": file_path,
                                "line_no": i + 1,
                                "key_type": api_key_name,
                                "value": line
                            })
            except:
                continue

def delete_folder_contents(folder):
    # Delete all the files and subdirectories in the folder
    for root, dirs, files in os.walk(folder):
        for f in files:
            os.unlink(os.path.join(root, f))
        for d in dirs:
            shutil.rmtree(os.path.join(root, d))



def home_page(request):
    if request.method == "GET":
        return render(request, "main.html")
    else:
        if 'zip_file' in request.POST:
            return redirect('/zip-vulnerability-checker')
        if 'github' in request.POST:
            return redirect('/repo-vulnerability-checker')
        if 'link' in request.POST:
            return redirect('/link-vulnerability-checker')



def zip_vulnerability_checker(request):
    if request.method == "GET":
        return render(request, "file.html")
    else:
        output = []
        if 'zip_file' in request.FILES:
            zip_file = ZipFile(request.FILES['zip_file'])
            zip_file.extractall("folder")
            zip_file.close()
            try:
                for key, value in _regex.items():
                    search_dir("folder/", value, key, output)
                delete_folder_contents("folder/")
                return render(request, "file.html", {"output": output, "size": len(output)})
            except:
                delete_folder_contents("folder/")
                print("Some error occoured!->views.py/line-82<-")

        else:
            delete_folder_contents("folder/")
            return render(request, "file.html")


def link_vulnerability_checker(request):
    if request.method == "GET":
        return render(request, "file2.html")
    else:
        data = request.POST
        output = find_vulnerabilities(data["link"], int(data["depth"]))

        return render(request, "file2.html", output)


def download_repo(repo_url):
    # Send a GET request to the GitHub API to retrieve the repository's zip file
    r = requests.get(f'{repo_url}/archive/master.zip')
    
    # Check if the request was successful
    if r.status_code == 200:
        # Save the zip file to a local file
        with open('github_repo/repo.zip', 'wb') as f:
            f.write(r.content)
        return True
    else:
        print(f'Failed to download repository: {r.status_code}')
        return False


def repo_vulnerability_checker(request):
    if request.method == "GET":
        return render(request, "file3.html")
    else:
        repo_link = request.POST["link"]
        if download_repo(repo_link):

            output = []
            zip_file = ZipFile("github_repo/repo.zip")
            zip_file.extractall("folder")
            zip_file.close()

            for key, value in _regex.items():
                search_dir("folder/", value, key, output)

            delete_folder_contents("folder/")
            return render(request, "file3.html", {"output": output, "size": len(output)})
        
        else:
            print("Unable to fetch repo, try again!")
            return render(request, "file3.html")





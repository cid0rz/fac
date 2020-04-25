import os
import shutil
import sys
import requests

url_stable = "https://factorio.com/get-download/stable/headless/linux64" # url to download latst-stable for future implementation
filename_tar = "linux64.tar"


def copyDirTree(root_src_dir,root_dst_dir):
    for src_dir, dirs, files in os.walk(root_src_dir):
        dst_dir = src_dir.replace(root_src_dir, root_dst_dir, 1)
        if not os.path.exists(dst_dir):
            os.makedirs(dst_dir)
        for file_ in files:
            src_file = os.path.join(src_dir, file_)
            dst_file = os.path.join(dst_dir, file_)
            if os.path.exists(dst_file):
                try:
                    os.remove(dst_file)
                except PermissionError as exc:
                    os.chmod(dst_file, stat.S_IWUSR)
                    os.remove(dst_file)
            shutil.copy(src_file, dst_dir)

def remove(path):
    if os.path.isfile(path) or os.path.islink(path):
        os.remove(path)  # remove the file
    elif os.path.isdir(path):
        shutil.rmtree(path)  # remove dir and all contains
    else:
        print(".")

def download(url, filename):
    with open(filename, 'wb') as f:
        response = requests.get(url, stream=True)
        total = response.headers.get('content-length')

        if total is None:
            f.write(response.content)
        else:
            downloaded = 0
            total = int(total)
            for data in response.iter_content(chunk_size=max(int(total/1000), 1024*1024)):
                downloaded += len(data)
                f.write(data)
                done = int(50*downloaded/total)
                sys.stdout.write('\r[{}{}]'.format('█' * done, '.' * (50-done)))
                sys.stdout.flush()
    sys.stdout.write('\n')

factorio_path = input('Specify Factorio path ex. \n "/home/user/factorio/" --> ')  # get factorio path
try:
    os.chdir(factorio_path)
except Exception as e:
    print("Path not found: " + factorio_path)
    print(e)
factorio_version = input('Factorio version \n ex. "0.18.xx" --> ')  # get factorio version
path_file = factorio_path+factorio_version

print("Factorio path : " + factorio_path)
print("Factorio version : " + factorio_version)
print("Temp folder : " + path_file)

url_latestexperimental = "https://factorio.com/get-download/" + factorio_version + "/headless/linux64"
download(url_latestexperimental,filename_tar)

try:
    remove(path_file + "/")
    os.mkdir(path_file)
    shutil.unpack_archive(factorio_path + filename_tar, path_file, "tar")
except OSError:
    print("Temp directory created... FAILED (%s) failed" % path_file)
else:
    print("Temp directory created... OK (%s) " % path_file)
try:
    dest = copyDirTree(path_file+"/factorio/", factorio_path)
except OSError as e:
    print("Destination path:")
try:
    remove(path_file+"/")
    remove(factorio_path + "/" + filename_tar)
    print('Copying new files... OK \nTemp files/directory deleted... OK')
    print("UPDATE COMPLETED.")
except:
    print("Temp files/directory deleted... ERROR")
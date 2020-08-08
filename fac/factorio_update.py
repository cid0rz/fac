import os
import shutil
import sys
import requests

filename_tar = "linux64.tar"

"""url return based on user_input """
##TODO: proper input filter expression
def version(input_user):
    url_stable = "https://factorio.com/get-download/stable/headless/linux64"
    url_experimental ="https://factorio.com/get-download/latest/headless/linux64 "
    if input_user.upper() == "S" or len(input_user) == 0:
        url = url_stable
        factorio_version = "stable"
        print("Latest stable version selected")
        return (factorio_version, url)
    elif input_user.upper() == "E":
        url = url_experimental
        factorio_version = "experimental"
        print("Latest exerimental version selected")
        return(factorio_version, url)
    elif len(input_user) != 0 and (input_user.upper() != "S" or input_user.upper() != "E"):
        factorio_version = input_user.lower()
        url = "https://factorio.com/get-download/" + factorio_version + "/headless/linux64"
        print( factorio_version + " version selected")
        return(factorio_version, url)
    else:
        print("At least one option must be selected. Terminating execution ")
        quit()

"""copying file function"""
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

""" remove file and directory function  """
def remove(path):
    if os.path.isfile(path) or os.path.islink(path):
        os.remove(path)  # remove the file
    elif os.path.isdir(path):
        shutil.rmtree(path)  # remove dir and all contains
    else:
        print(".")

""" download function with bar indication """
#FIXME: no detection of connection errors or bad url specified
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



factorio_path = input('Specify Factorio path ex. \n [/home/user/factorio/] --> ')  # get factorio path
try:
    os.chdir(factorio_path)
except Exception as e:
    print("Path not found: (" + factorio_path+")")
    print(e)
    quit()

version_url = version(input('Factorio version, type S for latest_stable, '
                            'E for latest_experimental or digit a specific version,'
                            ' otherwise stable will be installed. \n ex. [S/E/0.18.xx] --> '))  # get factorio version


""" download """
download(version_url[1],filename_tar)
path_file = factorio_path+version_url[0]
try:
    remove(path_file + "/")
    os.mkdir(path_file)
    shutil.unpack_archive(factorio_path + filename_tar, path_file, "tar")
except OSError:
    print("Temp directory created... FAILED (%s) failed" % path_file)
    quit()
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

exit()
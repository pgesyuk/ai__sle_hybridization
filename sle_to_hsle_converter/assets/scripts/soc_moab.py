import os, shutil
import subprocess
import re

def get_list_of_files_in_dir(dir, filter="*", basename=1):
    # print(f"Searching for files with name: {filter} in {dir}")
    (status, output) = subprocess.getstatusoutput(f"find {dir}/ -type f -maxdepth 1 -name '{filter}'")
    if status:
        raise AssertionError(f"failed to find files in {dir}")

    file_list = []
    for line in output.splitlines():
        item = os.path.basename(line) if basename == 1 else line
        file_list.append(item)

    # print("files found: \n%s" % "\n".join(file_list))
    return file_list

def get_dut_list(workarea):
    dut_list = []
    file_list = get_list_of_files_in_dir(dir=os.path.join(workarea, "cfg"), filter="*.design.cfg", basename=1)
    for file in file_list:
        dut_list.append(file.replace('.design.cfg', ''))
    return dut_list

def get_soc_file_list(workarea):
    file_list = []
    file_list = get_list_of_files_in_dir(dir=os.path.join(workarea, "filelists"), filter="*soc.list", basename=1)
    return file_list

def is_line_comment(line):
    return re.search('^\s*\/\/', line)

def is_line_empty(line):
    return line == ''

#######################################################################

workarea = os.getenv('WORKAREA')
if not workarea:
    raise AssertionError(f"WORKAREA is not defined!")

dut_list = get_dut_list(workarea)
soc_list = get_soc_file_list(workarea)

# GCD paths are only present in certain DUTs (e.g. nvlsi7); initialise to
# None so the cross-DUT GCD hack below is safely skipped when absent.
gcdu_path = None
gcds_path = None
gcdp_path = None

for dut in dut_list:
    print(f"Populating SOC softlink for {dut}")
    if f"{dut}.soc.list" in soc_list:
        dut_soc_file = f"{dut}.soc.list"
    else:
        dut_soc_file = "soc.list"

    soc_dut_path = os.path.join(workarea, "soc", dut)
    try: shutil.rmtree(soc_dut_path)
    except FileNotFoundError: pass

    os.makedirs(soc_dut_path, exist_ok=True)

    with open(os.path.join(workarea, "filelists", dut_soc_file), "r") as infile:
        for line in infile:
            if is_line_empty(line): continue
            if is_line_comment(line): continue
            ip_info = line.replace(" ", "").split(",")
            if ip_info:
                soc_path = os.path.join(workarea, "soc", dut, ip_info[0])
                #FIXME HACK - save GCD PATH to populate to OTHER DUT
                if ip_info[0] in ["gcdu"]:
                    gcdu_path = ip_info[1]
                if ip_info[0] in ["gcds"]:
                    gcds_path = ip_info[1]
                if ip_info[0] in ["gcdp"]:
                    gcdp_path = ip_info[1]

                try: os.unlink(soc_path)
                except FileNotFoundError: os.symlink(ip_info[1], soc_path)

                cdie_match = re.search(r"(cdie\d)", ip_info[0])
                if cdie_match:
                    cdie_path = os.path.join(workarea, "soc", dut, f"{cdie_match.group(0)}")
                    try: os.unlink(cdie_path)
                    except FileNotFoundError: os.symlink(soc_path, cdie_path)

##FIXME SPECIAL HACK FOR GCD ON OTHER DUT AS GCD ONLY APPEAR IN NVLSI7
for dut in dut_list:
    if gcdu_path is not None:
        soc_path = os.path.join(workarea, "soc", dut, "gcdu")
        if not os.path.islink(soc_path):
            os.symlink(gcdu_path, soc_path)
    if gcds_path is not None:
        soc_path = os.path.join(workarea, "soc", dut, "gcds")
        if not os.path.islink(soc_path):
            os.symlink(gcds_path, soc_path)
    if gcdp_path is not None:
        soc_path = os.path.join(workarea, "soc", dut, "gcdp")
        if not os.path.islink(soc_path):
            os.symlink(gcdp_path, soc_path)

print("Updating Done")

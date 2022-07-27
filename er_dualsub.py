import os, shutil, argparse, time
import subprocess
import xml.etree.ElementTree as ET

#list of files you want to mod
FILES = [
        {
            'msgbnd': 'menu.msgbnd',
            'fmg': ['LoadingTitle.fmg', 'LoadingText.fmg', 'GR_Dialogues.fmg', 'TalkMsg.fmg', 'BloodMsg.fmg'],
            'separator': ['/', None] + ['\n']*3
        },
        {
            'msgbnd': 'item.msgbnd',
            'fmg': ['AccessoryInfo.fmg', 'GemInfo.fmg', 'GoodsInfo.fmg', 'GoodsInfo2.fmg', 'ProtectorInfo.fmg', 'WeaponInfo.fmg'],
            'separator': ['\n']*6
        }
    ]

#constants
VERSION = '1.2'
YABBER_EXE = 'Yabber.exe'
YABBER_DCX_EXE = 'Yabber.DCX.exe'
LANG_DIRS = {
    'de': 'deude', #German
    'en': 'engus', #English
    'es-ar': 'spaar', #Spanish - Latin America
    'es-es': 'spasp', #Spanish - Spain
    'fr': 'frafr', #French
    'it': 'itait', #Italian
    'ja': 'jpnjp', #Japanese
    'ko': 'korkr', #Korean
    'pt-pt': 'polpl', #Polish
    'pt-br': 'polbr', #Portuguese - Brazil
    'ru': 'rusru', #Russian
    'th': 'thath', #Thai
    'zh-cn': 'zhocn', #Simplified Chinese
    'zh-tw': 'zhotw' #Traditional Chinese
    }

def get_lang_dir(lang):
    if lang not in LANG_DIRS:
        print(f'lang list: {LANG_DIRS}')
        raise RuntimeError(f'Unsupported language detected. ({lang})')
    return LANG_DIRS[lang]

def mkdir(dir):
    os.makedirs(dir, exist_ok=True)

#get arguments
def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('msg', help='path to msg folder')
    parser.add_argument('yabber', help='path to Yabber.exe')
    parser.add_argument('lang1', help='language 1')
    parser.add_argument('lang2', help='language 2')
    parser.add_argument('--mod_name', default=None, type=str, help='name of mod folder')
    parser.add_argument('--swap_files', action='store_true', help='swap files between 2 languages after making dualsub')
    parser.add_argument('--remove_lang2', action='store_true', help='remove files for lang2 after making dualsub')
    parser.add_argument('--debug', action='store_true', help='remain intermediate files like xml')
    parser.add_argument('--all', action='store_true', help='display all text in 2 languages')
    args = parser.parse_args()
    return args

#class for fmg xml
class FmgXml:
    def __init__(self, xml_path):
        self.xml_path = xml_path
        self.xml = ET.parse(xml_path)

    def write(self):
        self.xml.write(self.xml_path, xml_declaration=True, encoding='utf-8')
    
    def make_dualsub(xml1, xml2, separator, all=False):
        print(f'Making dualsub: {os.path.basename(xml1.xml_path)}...')
        if os.path.basename(xml1.xml_path)=='GR_Dialogues.fmg.xml':
            merge = FmgXml.merge_text_grdialog        
        else:
            merge = FmgXml.merge_text_std

        for xml1_e, xml2_e in zip(xml1.xml.getroot().find('entries'), xml2.xml.getroot().find('entries')):
            if xml1_e.text == '%null%' or xml2_e.text == '%null%':
                continue
            if xml1_e.text is None:
                xml1_e.text = ''
            if xml2_e.text is None:
                xml2_e.text = ''
            if xml1_e.attrib['id']!=xml2_e.attrib['id']:
                raise RuntimeError('ids are not the same.')
            t1, sep, t2 = merge(xml1_e.text, xml2_e.text, separator, xml1_e.attrib['id'], all)
            if sep is not None:
                xml1_e.text = t1 + sep + t2
                xml2_e.text = t2 + sep + t1

    def merge_text_std(t1, t2, sep, id, all):
        if t1.replace(' ', '').lower()==t2.replace(' ', '').lower() or (t1 in ['x', '×']):
            return None, None, None
        if sep is None:
            if '\n' in t1 or '\n' in t2:
                def remove_linefeed(text):
                    text_list = text.split('\n')
                    text_list = [t for t in text_list if t!='']
                    return '\n'.join(text_list)
                t1 = remove_linefeed(t1)
                t2 = remove_linefeed(t2)
                sep = '\n'
            else:
                sep='/'
        return t1, sep, t2

    def merge_text_grdialog(t1, t2, sep, id, all):
        if (len(id)<3 and not all) or (t1.replace(' ', '').lower()==t2.replace(' ', '').lower()):
            return None, None, None
        return t1, sep, t2

def run_yabber(yabber_exe, file):
    if not os.path.exists(file):
        RuntimeError(f'File not found. ({file})')
    proc = subprocess.Popen(('cmd', '/c', yabber_exe, file), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    proc.wait()
    (stdout, stderr) = proc.communicate()
    print(stdout[:-4].decode())

    if proc.returncode != 0:
        print(stderr.decode())
        RuntimeError('Yabber raised an unexpected error.')

if __name__=='__main__':
    args = get_args()
    start = time.time()

    #parameters
    msg_dir = args.msg
    yabber_dir = os.path.dirname(args.yabber)
    yabber = os.path.join(yabber_dir, YABBER_EXE)
    yabber_dcx = os.path.join(yabber_dir, YABBER_DCX_EXE)
    mod_name = args.mod_name
    lang1=args.lang1
    lang2=args.lang2
    lang_dirs = [get_lang_dir(lang) for lang in [lang1, lang2]]
    swap_files = args.swap_files
    remove_lang2 = args.remove_lang2
    debug = args.debug
    all = args.all
    if mod_name is None or mod_name=='':
        mod_name = f'dualsub_{lang1}_{lang2}' + '_all'*all + '_swap'*swap_files

    #check args
    if os.path.basename(args.yabber)!='Yabber.exe':
        raise RuntimeError(f'Not Yabber.exe ({args.yabber})')
    if not os.path.isdir(msg_dir):
        raise RuntimeError(f'Not a folder. ({msg_dir})')
    if lang1==lang2:
        raise RuntimeError(f'Langages are the same. ({lang1})')

    #check dll
    dll_path = os.path.join(os.path.dirname(args.yabber), 'lib', 'oo2core_6_win64.dll')
    if not os.path.exists(dll_path):
        raise RuntimeError(f'DLL not found. Copy it from Elden Ring. ({dll_path})')


    #print settings
    print(f'ER Dualsub Tool ver{VERSION}')
    print('Settings')
    print(f'  lang1: {lang1}')
    print(f'  lang2: {lang2}')
    print(f'  all: {all}')
    print(f'  swap_files: {swap_files}')
    print(f'  debug: {debug}\n')

    #make buckup
    print('Making backup: msg_backup')
    if os.path.exists(os.path.join('msg_backup', lang_dirs[0])):
        shutil.rmtree(os.path.join('msg_backup', lang_dirs[0]))
    if os.path.exists(os.path.join('msg_backup', lang_dirs[1])):
        shutil.rmtree(os.path.join('msg_backup', lang_dirs[1]))
    mkdir('msg_backup')
    shutil.copytree(os.path.join(msg_dir, lang_dirs[0]), os.path.join('msg_backup', lang_dirs[0]))
    shutil.copytree(os.path.join(msg_dir, lang_dirs[1]), os.path.join('msg_backup', lang_dirs[1]))

    #merge msgbnd
    for file in FILES:
        if len(file['msgbnd'])==0 and swap_files:
            continue
        dcx_path = [os.path.join(mod_name, 'msg', lang, file['msgbnd']+'.dcx') for lang in lang_dirs]
    
        #copy msgbnd.dcx
        for lang, dcx in zip(lang_dirs, dcx_path):
            mkdir(os.path.join(mod_name, 'msg', lang))
            shutil.copy(os.path.join(msg_dir, lang, file['msgbnd']+'.dcx'), dcx)

        #unpack dcx
        for dcx in dcx_path:
            run_yabber(yabber_dcx, dcx)

        #unpack msgbnd
        msgbnd_path = [dcx[:-4] for dcx in dcx_path]
        for msgbnd in msgbnd_path:
            run_yabber(yabber, msgbnd)

        #get fmg dir
        def get_fmg_path(xml_dir):
            xml = ET.parse(os.path.join(xml_dir, '_yabber-bnd4.xml'))
            files = xml.getroot().find('files')
            sample_path = files[0].find('path').text
            return os.path.dirname(sample_path)

        xml_dirs = [os.path.join(mod_name, 'msg', lang, file['msgbnd'].replace('.', '-')) for lang in lang_dirs]
        #'mod_name'/msg/'lang'/menu-msgbnd/GR/data/INTERROOT_win64/msg/'lang'
        fmg_dirs = [os.path.join(xml_dir, get_fmg_path(xml_dir)) for xml_dir in xml_dirs]

        def get_xml(fmg_dir, fmg):
            path = os.path.join(fmg_dir, fmg)
            if not os.path.exists(path):
                return None
            run_yabber(yabber, path)
            return FmgXml(path+'.xml')

        def pack_fmg(xml):
            xml.write()
            run_yabber(yabber, os.path.join(xml.xml_path))

        def merge_fmg(fmg, sep):
            xmls = [get_xml(fmg_dir, fmg) for fmg_dir in fmg_dirs]
            if None in xmls:
                raise RuntimeError(f'file not found. ({fmg})')
            FmgXml.make_dualsub(xmls[0], xmls[1], sep, all=all)
            [pack_fmg(xml) for xml in xmls]

        #merge fmg
        for fmg, sep in zip(file['fmg'], file['separator']):
            merge_fmg(fmg, sep)

        if all:
            fmgs = os.listdir(fmg_dirs[0])
            fmgs = [f for f in fmgs if (f not in file['fmg']) and f[-4:]=='.fmg']
            path_exists = [[os.path.exists(os.path.join(fmg_dir, fmg)) for fmg_dir in fmg_dirs] for fmg in fmgs]
            fmgs = [f for f, p in zip(fmgs, path_exists) if p[0] and p[1]]

            list(map(lambda x: merge_fmg(x, None), fmgs))

        #swap fmg files between 2 languages        
        if swap_files:
            print('Swapping files')
            fmg_dir1 = fmg_dirs[0]
            fmg_dir2 = fmg_dirs[1]
            shutil.move(fmg_dir1, fmg_dir1+'temp')
            shutil.move(fmg_dir2, fmg_dir1)
            shutil.move(fmg_dir1+'temp', fmg_dir2)

        #remove files for lang2
        if remove_lang2:
            print('Removing files for lang2')
            shutil.rmtree(os.path.join(mod_name, 'msg', lang_dirs[1]))
            xml_dirs=[xml_dirs[0]]
            msgnd_path=[msgbnd_path[0]]

        #repack msgbnd 
        for xml_dir, msgbnd in zip(xml_dirs, msgbnd_path):
            run_yabber(yabber, xml_dir)
            run_yabber(yabber_dcx, msgbnd)

        #remove unnecessary files
        if not debug:
            print('Removing unnecessary files')
            for xml_dir, msgbnd in zip(xml_dirs, msgbnd_path):
                os.remove(msgbnd)
                os.remove(msgbnd+'.bak')
                os.remove(msgbnd+'.dcx.bak')
                os.remove(msgbnd+'-yabber-dcx.xml')
                shutil.rmtree(xml_dir)

    print(f'Run time (s): {time.time()-start}')

    print(f'Done! "{mod_name}" is the mod folder')

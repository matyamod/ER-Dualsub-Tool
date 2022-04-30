import os, shutil, argparse, time
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
        print('lang list: {}'.format(LANG_DIRS))
        raise RuntimeError('Unsupported language detected. ({})'.format(lang))
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
        print('Making dualsub: {}\n'.format(os.path.basename(xml1.xml_path)))
        if os.path.basename(xml1.xml_path)=='GR_Dialogues.fmg.xml':
            merge = FmgXml.merge_text_grdialog        
        else:
            merge = FmgXml.merge_text_std

        for xml1_e, xml2_e in zip(xml1.xml.getroot().find('entries'), xml2.xml.getroot().find('entries')):
            if xml1_e.text == '%null%' or xml2_e.text == '%null%':
                continue
            if xml1_e.attrib['id']!=xml2_e.attrib['id']:
                raise RuntimeError('ids are not the same.')
            t1, sep, t2 = merge(xml1_e.text, xml2_e.text, separator, xml1_e.attrib['id'], all)
            xml1_e.text = t1 + sep + t2
            xml2_e.text = t2 + sep + t1

    def merge_text_std(t1, t2, sep, id, all):
        if len(t1)<10 and t1.replace(' ', '').lower()==t2.replace(' ', '').lower():
            return t1, '', ''
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
        if (len(id)<3 and not all) or (len(t1)<10 and t1.replace(' ', '').lower()==t2.replace(' ', '').lower()):
            return t1, '', ''
        return t1, sep, t2

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
        if swap_files:
            mod_name = 'dualsub_{}_{}'.format(lang2, lang1) + '_all'*all
        else:
            mod_name = 'dualsub_{}_{}'.format(lang1, lang2) + '_all'*all

    #check args
    if os.path.basename(args.yabber)!='Yabber.exe':
        raise RuntimeError('Not Yabber.exe ({})'.format(args.yabber))
    if os.path.basename(msg_dir)!='msg':
        raise RuntimeError('Not msg folder ({})'.format(msg_dir))
    if lang1==lang2:
        raise RuntimeError('Langages are the same. ({})'.format(lang1))

    #print settings
    print('ER Dualsub Tool ver1.0')
    print('Settings')
    print('  lang1: {}'.format(lang1))
    print('  lang2: {}'.format(lang2))
    print('  all: {}'.format(all))
    print('  swap_files: {}'.format(swap_files))
    print('  debug: {}\n'.format(debug))

    #make buckup
    print('Making backup: msg_backup\n')
    if os.path.exists('msg_backup'):
        shutil.rmtree('msg_backup')
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
            os.system(yabber_dcx + ' ' + dcx)

        #unpack msgbnd
        msgbnd_path = [dcx[:-4] for dcx in dcx_path]
        for msgbnd in msgbnd_path:
            os.system(yabber + ' ' + msgbnd)

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
            os.system(yabber + ' ' + path)
            return FmgXml(path+'.xml')

        def pack_fmg(xml):
            xml.write()
            os.system(yabber + ' ' + os.path.join(xml.xml_path))

        def merge_fmg(fmg, sep):
            xmls = [get_xml(fmg_dir, fmg) for fmg_dir in fmg_dirs]
            FmgXml.make_dualsub(xmls[0], xmls[1], sep, all=all)
            [pack_fmg(xml) for xml in xmls]

        #merge fmg
        for fmg, sep in zip(file['fmg'], file['separator']):
            merge_fmg(fmg, sep)

        if all:
            fmgs = os.listdir(fmg_dirs[0])
            fmgs = [f for f in fmgs if (f not in file['fmg']) and f[-4:]=='.fmg']
            list(map(lambda x: merge_fmg(x, None), fmgs))

        #swap fmg files between 2 languages        
        if swap_files:
            print('Swapping files\n')
            fmg_dir1 = fmg_dirs[0]
            fmg_dir2 = fmg_dirs[1]
            shutil.move(fmg_dir1, fmg_dir1+'temp')
            shutil.move(fmg_dir2, fmg_dir1)
            shutil.move(fmg_dir1+'temp', fmg_dir2)

        #remove files for lang2
        if remove_lang2:
            print('Removing files for lang2\n')
            shutil.rmtree(os.path.join(mod_name, 'msg', lang_dirs[1]))
            xml_dirs=[xml_dirs[0]]
            msgnd_path=[msgbnd_path[0]]

        #repack msgbnd 
        for xml_dir, msgbnd in zip(xml_dirs, msgbnd_path):
            os.system(yabber + ' ' + xml_dir)
            os.system(yabber_dcx + ' ' + msgbnd)

        #remove unnecessary files
        if debug:
            print('Removing unnecessary files\n')
            for xml_dir, msgbnd in zip(xml_dirs, msgbnd_path):
                os.remove(msgbnd)
                os.remove(msgbnd+'.bak')
                os.remove(msgbnd+'.dcx.bak')
                os.remove(msgbnd+'-yabber-dcx.xml')
                shutil.rmtree(xml_dir)

    print('Run time (s): {}'.format(time.time()-start))

    print('Done! "{}" is the mod folder'.format(mod_name))

from __future__ import print_function
import os
import sys
import shutil
import pymake
import flopy

# define program data
target = 'mt3dusgs'
if sys.platform.lower() == 'win32':
    target += '.exe'

# get program dictionary
prog_dict = pymake.usgs_program_data.get_target(target)

# set up paths
dstpth = os.path.join('temp')
if not os.path.exists(dstpth):
    os.makedirs(dstpth)

mtusgsver = prog_dict.version
mtusgspth = os.path.join(dstpth, prog_dict.dirname)
emtusgs = os.path.abspath(os.path.join(dstpth, target))

mfnwt_target = 'mfnwt'
temp_dict = pymake.usgs_program_data().get_target(mfnwt_target)
mfnwtpth = os.path.join(dstpth, temp_dict.dirname)
emfnwt = os.path.abspath(os.path.join(dstpth, mfnwt_target))

mf6_target = 'mf6'
temp_dict = pymake.usgs_program_data().get_target(mf6_target)
mf6pth = os.path.join(dstpth, temp_dict.dirname)
emf6 = os.path.abspath(os.path.join(dstpth, mf6_target))

if sys.platform.lower() == 'win32':
    emfnwt += '.exe'
    emf6 += '.exe'


# example path
expth = os.path.join(mtusgspth, 'data')

# set up pths and exes
pths = [mtusgspth, mfnwtpth, mf6pth]
exes = [emtusgs, emfnwt, emf6]


def get_example_dirs():
    if os.path.exists(emtusgs):
        exclude_dirs = ['Keating', 'Keating_UZF']

        upd = pymake.usgs_program_data()

        # exclude additional directories based on version of codes
        # MODFLOW-NWT
        ver = upd.get_version('mfnwt')
        if ver == '1.2.0':
            exclude_dirs += ['UZT_NonLin',
                             'UZT_Disp_Lamb01_TVD',
                             'UZT_Disp_Lamb1',
                             'UZT_Disp_Lamb10']

        # create list of example directories to test
        exdirs = [o for o in sorted(os.listdir(expth))
                  if os.path.isdir(os.path.join(expth, o)) and
                  o not in exclude_dirs]
    else:
        exdirs = [None]
    return exdirs


def run_mt3dusgs(temp_dir):
    if os.path.exists(emtusgs):
        model_ws = os.path.join(expth, temp_dir)

        files = [f for f in os.listdir(model_ws)
                 if os.path.isfile(os.path.join(model_ws, f))]

        mf_nam = None
        mt_nam = None
        flow_model = None
        for f in files:
            if '_mf.nam' in f.lower():
                mf_nam = f
                flow_model = 'mfnwt'
            if '_mt.nam' in f.lower():
                mt_nam = f
            if f == 'mfsim.nam':
                mf_nam = f
                flow_model = 'mf6'

        msg = 'A MODFLOW name file not present in {}'.format(model_ws)
        assert mf_nam is not None, msg

        msg = 'A MT3D-USGS name file not present in {}'.format(model_ws)
        assert mt_nam is not None, msg

        # run the flow model
        msg = '{}'.format(emfnwt)
        if mf_nam is not None:
            msg += ' {}'.format(os.path.basename(mf_nam))
        if flow_model == 'mfnwt':
            nam = mf_nam
            eapp = emfnwt
        elif flow_model == 'mf6':
            nam = None
            eapp = emf6
        success, buff = flopy.run_model(eapp, nam, model_ws=model_ws,
                                        silent=False)

        assert success, 'could not run...{}'.format(msg)

        # run the MT3D-USGS model
        print('running model...{}'.format(mt_nam))
        success, buff = flopy.run_model(emtusgs, mt_nam,
                                        model_ws=model_ws, silent=False,
                                        normal_msg='Program completed.')
        if not success:
            errmsg = 'could not run {}'.format(mtnam)
    else:
        success = False
        errmsg = 'could not run {}'.format(os.path.basename(emtusgs))

    assert success, errmsg

    return


def clean_up(pth, exe):
    # clean up downloaded directories
    if os.path.isdir(pth):
        print('Removing folder ' + pth)
        shutil.rmtree(pth)

    # clean up compiled executables
    if os.path.isfile(exe):
        print('Removing ' + exe)
        os.remove(exe)
    return


def test_download_exes():
    pymake.getmfexes(dstpth, exes=('mfnwt', 'mf6'))
    return


def test_compile_mt3dusgs():
    # Remove the existing MT3D-USGS directory if it exists
    if os.path.isdir(mtusgspth):
        shutil.rmtree(mtusgspth)

    # download and compile MT3D-USGS
    pymake.build_program(target=target,
                         download_dir=dstpth,
                         exe_dir=dstpth)
    return


def test_mt3dusgs():
    example_dirs = get_example_dirs()
    for dn in example_dirs:
        yield run_mt3dusgs, dn


def test_clean_up():
    for pth, exe in zip(pths, exes):
        yield clean_up, pth, exe
    return


if __name__ == "__main__":
    # download mfnwt and mf6
    test_download_exes()

    # compile MT3D-USGS
    test_compile_mt3dusgs()

    # get name files and simulation name
    example_dirs = get_example_dirs()

    # run example problems
    for dn in example_dirs:
        run_mt3dusgs(dn)

    # clean up test
    for pth, exe in zip(pths, exes):
        clean_up(pth, exe)

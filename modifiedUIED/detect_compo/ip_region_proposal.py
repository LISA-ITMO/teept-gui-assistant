import cv2
from os.path import join as pjoin
import json
import numpy as np

import detect_compo.lib_ip.ip_preprocessing as pre
import detect_compo.lib_ip.ip_draw as draw
import detect_compo.lib_ip.ip_detection as det
import detect_compo.lib_ip.file_utils as file
import detect_compo.lib_ip.Component as Compo
from UIED_config.CONFIG_UIED import Config
C = Config()


def nesting_inspection(org, grey, compos, ffl_block):
    '''
    Inspect all big compos through block division by flood-fill
    :param ffl_block: gradient threshold for flood-fill
    :return: nesting compos
    '''
    nesting_compos = []
    for i, compo in enumerate(compos):
        if compo.height > 50:
            replace = False
            clip_grey = compo.compo_clipping(grey)
            n_compos = det.nested_components_detection(clip_grey, org, grad_thresh=ffl_block, show=False)
            Compo.cvt_compos_relative_pos(n_compos, compo.bbox.col_min, compo.bbox.row_min)

            for n_compo in n_compos:
                if n_compo.redundant:
                    compos[i] = n_compo
                    replace = True
                    break
            if not replace:
                nesting_compos += n_compos
    return nesting_compos


def to_arr(compos):
    img_shape = compos[0].image_shape
    output = {'img_shape': img_shape, 'compos': []}

    for compo in compos:
        c = {'id': compo.id, 'class': compo.category}
        (c['column_min'], c['row_min'], c['column_max'], c['row_max']) = compo.put_bbox()
        c['width'] = compo.width
        c['height'] = compo.height
        output['compos'].append(c)

    return output

def compo_detection(input_img, uied_params, resize_by_height=800, classifier=None, show=False, wai_key=0):
    # Определяем имя файла (или имя по умолчанию для np.array)
    if isinstance(input_img, str):
        name = input_img.split('/')[-1][:-4] if '/' in input_img else input_img.split('\\')[-1][:-4]
        img, grey = pre.read_img(input_img, resize_by_height)  # This returns img and gray
    else:
        name = "captured_image"
        img = pre.resize_img(input_img, resize_by_height)  # This returns only the resized image
        grey = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)  # Convert to grayscale manually

    # Create directory for output
    #
    # ip_root = file.build_directory(pjoin(output_root, "ip"))

    # Image binarization
    binary = pre.binarization(img, grad_min=int(uied_params['min-grad']))
    det.rm_line(binary, show=show, wait_key=wai_key)

    # Component detection and filtering
    uicompos = det.component_detection(binary, min_obj_area=int(uied_params['min-ele-area']))
    uicompos = det.compo_filter(uicompos, min_area=int(uied_params['min-ele-area']), img_shape=binary.shape)
    uicompos = det.merge_intersected_compos(uicompos)
    det.compo_block_recognition(binary, uicompos)

    # Check for nested components
    if uied_params['merge-contained-ele']:
        uicompos = det.rm_contained_compos_not_in_block(uicompos)

    # Update component information
    Compo.compos_update(uicompos, img.shape)
    Compo.compos_containment(uicompos)
    uicompos += nesting_inspection(img, grey, uicompos, ffl_block=uied_params['ffl-block'])
    Compo.compos_update(uicompos, img.shape)

    # Draw and save results
   # draw.draw_bounding_box(img, uicompos, show=show, name='merged compo', write_path=pjoin(ip_root, name + '.jpg'), wait_key=wai_key)
    Compo.compos_update(uicompos, img.shape)
    arr = to_arr(uicompos)

    #print("Input: %s Output: %s" % (name, pjoin(ip_root, name + '.json')))
    return arr

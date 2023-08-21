import scyjava
import imagej
import openflexure_microscope_client as ofm_client
from ofm_utils import capture_full_image
from time import sleep
import cv2
import numpy

def run_imgj():
    scyjava.config.add_option('-Xmx100g')
    ij = imagej.init("Fiji.app")
    print(ij.getVersion())

    grid_size_x = 10
    grid_size_y = 25
    tile_overlap = 35
    image_path = "../d_set"
    image_name = '{iiii}.png'
    output_path = "../d_set"

    stitching_macro = f"""run("Grid/Collection stitching", "type=[Grid: snake by rows] order=[Left & Up] grid_size_x={grid_size_x} grid_size_y={grid_size_y} tile_overlap={tile_overlap} first_file_index_i=1 directory=[{image_path}] file_names={image_name} output_textfile_name=TileConfiguration.txt fusion_method=[Linear Blending] regression_threshold=0.30 max/avg_displacement_threshold=2.50 absolute_displacement_threshold=3.50 compute_overlap use_virtual_input_images computation_parameters=[Save memory (but be slower)] image_output=[Write to disk] output_directory=[{output_path}]");"""

    merge_macro = f"""open("{image_path}/img_t1_z1_c1");
        open("{image_path}/img_t1_z1_c2");
        open("{image_path}/img_t1_z1_c3");
        selectImage("img_t1_z1_c3");
        selectImage("img_t1_z1_c2");
        selectImage("img_t1_z1_c3");
        run("Merge Channels...", "c1=img_t1_z1_c1 c2=img_t1_z1_c2 c3=img_t1_z1_c3 create");
        saveAs("PNG", "{image_path}/Composite.png");"""

    _=ij.py.run_macro(stitching_macro)
    _=ij.py.run_macro(merge_macro)

#Up and to the left snake by rows
#35% overlap
#start by moving to bottom right
#78200 length across y axis
def snake_img_cap(def_x_step=1600, def_y_step = 1600, takes = 3, y_moves = 25, x_moves = 10, quality = 80):
    microscope, original_position = set_up_microscope()

    img_count = 0
    x_direction = 'pos'
    for i in range(0, y_moves):
        for j in range(0, x_moves):
            img_count += 1
            count_str = str(img_count)
            for k in range(0, 4-len(count_str)):
                count_str = '0' + count_str

            img = capture_images(microscope, takes)
            img.save(f'd_set/{count_str}.png')
            print(j, i, "Direction:", x_direction)
            if j != x_moves-1:
                move_x_pos(microscope, x_direction, def_x_step)
        x_direction = reverse_direction(x_direction)
        move_y_pos(microscope, def_y_step)
    microscope.move(original_position)

def set_up_microscope():
    microscope = ofm_client.find_first_microscope()
    original_position = microscope.position.copy()
    return microscope, original_position

def reverse_direction(direction):
    if direction == 'pos':
        direction = 'neg'
    elif direction == 'neg':
        direction = 'pos'
    return direction

def move_x_pos(microscope, direction, x_step):
    pos = microscope.position
    if direction == 'pos':
        pos['x'] += x_step
    if direction == 'neg':
        pos['x'] -= x_step
    microscope.move(pos)

def move_y_pos(microscope, y_step):
    pos = microscope.position
    pos['y'] += y_step
    microscope.move(pos)

def capture_images(microscope, takes):
    imgs = []
    microscope.autofocus()
    img = run_img_cap(microscope)
    imgs.append(img)
    for i in range(0, takes-1):
        microscope.laplacian_autofocus({})
        img = run_img_cap(microscope)
        imgs.append(img)
    img = least_blurry(imgs)
    return img
    #return img with lowest laplace try to sticth...

def least_blurry(imgs):
    least_blurry = ''
    least_blurry_value = 0
    for img in imgs:
        cv2img = pil_to_cv2(img)
        gray = cv2.cvtColor(cv2img, cv2.COLOR_BGR2GRAY)
        laplace = cv2.Laplacian(gray, cv2.CV_64F).var()
        if laplace > least_blurry_value:
            least_blurry = img
            least_blurry_value = laplace
    return least_blurry

def run_img_cap(microscope):
    img = None
    while img == None:
        try:
            img = capture_full_image(microscope)
        except Exception as e:
            sleep(2)
            print(e)
    return img

def pil_to_cv2(img):
    pil_image = img.convert('RGB')
    open_cv_image = numpy.array(pil_image)
    # Convert RGB to BGR
    open_cv_image = open_cv_image[:, :, ::-1].copy()
    return open_cv_image

snake_img_cap()
#run_imgj()

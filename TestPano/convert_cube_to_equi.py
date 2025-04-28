import cv2
import numpy as np
import os

def load_face_images(base_path):
    faces = {}
    face_names = ['right', 'left', 'top', 'bottom', 'front', 'back']
    folder_names = {'r': 'right', 'l': 'left', 'u': 'top', 'd': 'bottom', 'f': 'front', 'b': 'back'}

    for short, full in folder_names.items():
        path = os.path.join(base_path, f'{short}.jpg')
        if not os.path.exists(path):
            raise FileNotFoundError(f"Missing face image: {path}")
        faces[full] = cv2.imread(path, cv2.IMREAD_COLOR)

    return faces

def vector_to_face(x, y, z):
    absX, absY, absZ = abs(x), abs(y), abs(z)
    isXPositive = x > 0
    isYPositive = y > 0
    isZPositive = z > 0

    maxAxis = max(absX, absY, absZ)

    if maxAxis == absX:
        if isXPositive:
            face = 'right'
        else:
            face = 'left'
    elif maxAxis == absY:
        if isYPositive:
            face = 'top'
        else:
            face = 'bottom'
    else:
        if isZPositive:
            face = 'front'
        else:
            face = 'back'
    return face

def convert_cube_to_equirectangular(input_folder, output_path, width=8192, height=4096):
    faces = load_face_images(input_folder)

    output = np.zeros((height, width, 3), dtype=np.uint8)

    for y in range(height):
        for x in range(width):
            theta = (x / width) * 2 * np.pi - np.pi
            phi = ((height - y) / height) * np.pi - (np.pi / 2)

            vx = np.cos(phi) * np.sin(theta)
            vy = np.sin(phi)
            vz = np.cos(phi) * np.cos(theta)

            face = vector_to_face(vx, vy, vz)
            img = faces[face]

            absVx, absVy, absVz = abs(vx), abs(vy), abs(vz)
            if face == 'right':
                sc = np.array([-vz, vy, -vx])
            elif face == 'left':
                sc = np.array([vz, vy, vx])
            elif face == 'top':
                sc = np.array([vx, vz, vy])
            elif face == 'bottom':
                sc = np.array([vx, -vz, -vy])
            elif face == 'front':
                sc = np.array([vx, vy, vz])
            else:
                sc = np.array([-vx, vy, -vz])

            sc = sc / np.max(np.abs(sc))

            ix = (sc[0] + 1) / 2 * (img.shape[1] - 1)
            iy = (1 - (sc[1] + 1) / 2) * (img.shape[0] - 1)

            ix = np.clip(ix, 0, img.shape[1] - 1)
            iy = np.clip(iy, 0, img.shape[0] - 1)

            output[y, x] = img[int(iy), int(ix)]

    cv2.imwrite(output_path, output)
    print(f"Saved Equirectangular Panorama at {output_path}")

if __name__ == "__main__":
    # Ví dụ sử dụng
    input_folder = "./cube_faces"  # Thư mục chứa l.jpg, r.jpg, f.jpg, b.jpg, u.jpg, d.jpg
    output_path = "./equirectangular_output.jpg"
    convert_cube_to_equirectangular(input_folder, output_path)

import os
from PIL import Image

def stitch_face(face_folder, face_short_name):
    levels = [d for d in os.listdir(face_folder) if os.path.isdir(os.path.join(face_folder, d))]
    if not levels:
        raise ValueError(f"No level folders found in {face_folder}")

    levels.sort()
    highest_level = levels[-1]

    level_path = os.path.join(face_folder, highest_level)

    tile_map = {}
    for root, dirs, files in os.walk(level_path):
        for file in files:
            if file.lower().endswith(('.jpg', '.jpeg', '.png', '.webp')):
                name = os.path.splitext(file)[0]
                parts = name.split('_')
                numbers = [p for p in parts if p.isdigit()]
                if len(numbers) >= 2:
                    y, x = map(int, numbers[-2:])
                    tile_map[(y, x)] = os.path.join(root, file)

    rows = [coord[0] for coord in tile_map.keys()]
    cols = [coord[1] for coord in tile_map.keys()]
    max_row = max(rows)
    max_col = max(cols)

    sample_tile = Image.open(next(iter(tile_map.values())))
    tile_width, tile_height = sample_tile.size

    face_image = Image.new('RGB', (max_col * tile_width, max_row * tile_height))

    for (y, x), filepath in tile_map.items():
        tile = Image.open(filepath)
        face_image.paste(tile, ((x - 1) * tile_width, (y - 1) * tile_height))

    output_name = f"./cube_faces/{face_short_name}.jpg"
    os.makedirs("./cube_faces", exist_ok=True)
    face_image.save(output_name)
    print(f"Saved {output_name}")

def rotate_faces():
    u_img = Image.open('./cube_faces/u.jpg')
    u_img = u_img.rotate(-180, expand=True)
    u_img.save('./cube_faces/u.jpg')

    d_img = Image.open('./cube_faces/d.jpg')
    d_img = d_img.rotate(180, expand=True)
    d_img.save('./cube_faces/d.jpg')

def flip_faces():
    u_img = Image.open('./cube_faces/u.jpg')
    u_img = u_img.transpose(Image.FLIP_LEFT_RIGHT)
    u_img.save('./cube_faces/u.jpg')

    d_img = Image.open('./cube_faces/d.jpg')
    d_img = d_img.transpose(Image.FLIP_LEFT_RIGHT)
    d_img.save('./cube_faces/d.jpg')

if __name__ == "__main__":
    faces = ['l', 'r', 'f', 'b', 'u', 'd']
    for face in faces:
        folder = os.path.join('./tiles', face)
        stitch_face(folder, face)

    rotate_faces()
    flip_faces()

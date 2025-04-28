from PIL import Image

img = Image.open('./cube_faces/u.jpg')
img = img.transpose(Image.FLIP_LEFT_RIGHT)
img.save('./cube_faces/u.jpg')

img = Image.open('./cube_faces/d.jpg')
img = img.transpose(Image.FLIP_LEFT_RIGHT)
img.save('./cube_faces/d.jpg')

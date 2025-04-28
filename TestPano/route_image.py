from PIL import Image

img = Image.open('./cube_faces/u.jpg')
img = img.rotate(-180, expand=True)  # hoặc 90, thử cả hai để đúng hướng
img.save('./cube_faces/u.jpg')

img = Image.open('./cube_faces/d.jpg')
img = img.rotate(180, expand=True)   # hoặc -90, thử cả hai để đúng hướng
img.save('./cube_faces/d.jpg')

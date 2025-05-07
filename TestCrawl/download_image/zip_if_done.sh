#!/bin/bash
BASE_DIR="/home/c006-staging/Panorama_VR_Crawl/TestCrawl/download_image"
STRUCTURE_DIR="$BASE_DIR/output_structure"
IMAGE_DIR="$BASE_DIR/image_crawled"

for txt_file in "$STRUCTURE_DIR"/*.txt; do
    if [ ! -s "$txt_file" ]; then
        basename=$(basename "$txt_file" .txt)
        image_folder="$IMAGE_DIR/$basename"

        if [ -d "$image_folder" ]; then
            zip_file="$IMAGE_DIR/${basename}.zip"
            if [ ! -f "$zip_file" ]; then
                echo "Zipping $image_folder -> $zip_file"
                zip -r "$zip_file" "$image_folder" && rm -rf "$image_folder"
            else
                echo "$zip_file already exists. Skipping."
            fi
        else
            echo "Folder $image_folder not found."
        fi
    fi
done

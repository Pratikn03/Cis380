# Clothing image dataset layout (optional)

This repo can be extended to support **image-based recognition** (brand/category) using a labeled ImageFolder dataset.
This is optional and not part of the default demo runtime.

## Where to put images

Place your dataset under:

- `data/raw/clothing_images/`

Recommended structure (folder-per-class):

```
data/raw/clothing_images/
  brand/
    train/
      nike/
        img001.jpg
        img002.jpg
      adidas/
        img010.jpg
    val/
      nike/
      adidas/
    test/
      nike/
      adidas/

  category/
    train/
      hoodie/
      jeans/
      sneakers/
    val/
    test/
```

If you only want to classify **brand**, you only need the `brand/` subtree.
If you only want **category**, you only need the `category/` subtree.

## Label rules

- The **folder name** is the class label.
- Supported image types: `.jpg`, `.jpeg`, `.png`, `.webp`

## Notes

- Large image datasets should not be committed to Git.
- Keep the training artifacts under:
  - `models/vision_brand/` (brand classifier)
  - `models/vision_category/` (category classifier)

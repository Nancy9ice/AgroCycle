# Requirements

- The photo is always labelled with its flight date(s), the Observed-product evidence label and its source, and says it is one day and not a crop map.
- It is never used as crop ground truth and never feeds the comparison.
- A photo is shown only if its checksum matches `naip_tiles`. A missing, unreadable or mismatched chip is reported, not replaced by a blank or another field's picture.
- No photo (file mode, no S3, or a field not in the index) hides the toggle; a service failure shows "Aerial photos are not available right now".
- The API never reads S3 keys outside `raw/naip/`.
- The toggle is at least 44 px tall and works by keyboard.

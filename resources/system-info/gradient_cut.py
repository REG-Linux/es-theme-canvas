"""Cut a smooth (gradient) studio background: each row's background colour comes
from the image's left and right edges; pixels near it that connect to the border
go transparent."""
import sys
import numpy as np
from PIL import Image
from scipy import ndimage

src, out, tol = sys.argv[1], sys.argv[2], float(sys.argv[3]) if len(sys.argv) > 3 else 14
img = np.asarray(Image.open(src).convert("RGB")).astype(np.float32)
h, w, _ = img.shape
edge = max(4, w // 60)
bg_row = np.median(np.concatenate([img[:, :edge], img[:, -edge:]], axis=1), axis=1)   # (h, 3)
bg_row = ndimage.uniform_filter1d(bg_row, size=9, axis=0)
diff = np.abs(img - bg_row[:, None, :]).max(axis=2)
near = diff < tol
labels, _ = ndimage.label(near)
border = np.unique(np.concatenate([labels[0], labels[-1], labels[:, 0], labels[:, -1]]))
bg = np.isin(labels, border[border > 0])
bg = ndimage.binary_opening(bg, iterations=1)
bg[:2], bg[-2:], bg[:, :2], bg[:, -2:] = True, True, True, True   # (the opening erodes the frame)
alpha = np.where(bg, 0, 255).astype(np.float32)
alpha = ndimage.gaussian_filter(alpha, 0.8)          # soft edge
rgba = np.dstack([img, alpha]).clip(0, 255).astype(np.uint8)
ys, xs = np.nonzero(alpha > 24)                      # crop to the device
pad = 4
rgba = rgba[max(0, ys.min() - pad):ys.max() + pad + 1, max(0, xs.min() - pad):xs.max() + pad + 1]
Image.fromarray(rgba, "RGBA").save(out)

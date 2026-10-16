import sys
from PIL import Image
def grid(names, out, cols=2, d='../../mc_out/sc/preview'):
    ims = [Image.open(f'{d}/{n}.png') for n in names]
    W, H = ims[0].size
    rows = (len(ims) + cols - 1) // cols
    g = Image.new('RGB', (W * cols, H * rows), (30, 30, 36))
    for i, im in enumerate(ims):
        g.paste(im, ((i % cols) * W, (i // cols) * H))
    g.save(out)
if __name__ == '__main__':
    grid(sys.argv[2:], sys.argv[1])

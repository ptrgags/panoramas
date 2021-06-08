# Panoramas (2021)

Utility Scripts for working with 360° panorama images. Some scripts are
designed specifically for interoperability with
[CesiumJS](https://github.com/CesiumGS/cesium).

I made these scripts for my own artistic uses. These scripts are written simply
with little error checking. This is not intended for production use.

## Usage

Basic Usage:

```
python main.py input_panorama.jpg
```

This script converts a 360° panorama in equirectangular projection, i.e.
`(longitude, latitude)`, to a cubemap for use as a skybox or environment map.

Input example:
![Input Panorama](figures/input_panorama.jpg)

Output example:
![Output Cubemap](figures/output_cubemap.png)

Note: the output is 6 images. They are labeled according to a z-up coordinate system compatible with the skybox in CesiumJS (See [SkyBox documentation](https://cesium.com/docs/cesiumjs-ref-doc/SkyBox.html?classFilter=skybox))

### Visualizing output

To view the output cubemap, run `panorama_to_cubemap.py` with the default
settings. This will create images like `output/skybox${faceName}.png`. These
can be viewed with the provided viewer in `index.html`. To do so, serve this
repo as a static site, e.g. with `http-server` (a NodeJS package)
or `python -m http.server` (Python3 built-in module) since browsers may block
the images otherwise.

![CesiumJS Viewer Example](figures/cesium-viewer.png)
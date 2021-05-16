# Panoramas (2021)

Utility Scripts for working with 360° panorama images. Some scripts are
designed specifically for interoperability with [CesiumJS](https://github.com/CesiumGS/cesium).

I made these scripts for my own artistic uses. These scripts are written simply
with little error checking. This is not intended for production use.

## `panorama_to_cubemap.py`

Basic Usage:

```
python panorama_to_cubemap.py input_panorama.jpg
```

This script converts a 360° panorama in equirectangular projection, i.e. `(longitude, latitude)`, to a cubemap for use as a skybox or environment map.

Input example:
![Input Panorama](figures/input_panorama.jpg)

Output example:
![Output Cubemap](figures/output_cubemap.png)

You'll notice that this cubemap has an unusual arrangement relative to
[what OpenGL/WebGL uses](https://www.khronos.org/opengl/wiki/Cubemap_Texture#Upload_and_orientation). This is because I intend to use this
for artistic skyboxes in CesiumJS. Cesium uses a z-up, right handed coordinate system (True Equator Mean Equinox) [according to the docs](https://cesium.com/docs/cesiumjs-ref-doc/SkyBox.html?classFilter=skybox)

TODO: Mini Cesium viewer
TODO: Screenshot
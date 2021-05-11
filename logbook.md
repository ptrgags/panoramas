# Panorama to Cubemap

## 2021-05-08 Setup

Today I set up the repo and started to implement the reprojection. I learned
that OpenCV has a `remap()` function that handles the image warping, you
just need to provide the indices. I'll need to refresh my memory of NumPy
arrays to do this

## 2021-05-09 Made a cubemap... but which way is up?

Today I got the code working to produce 6 images for a seamless cubemap, that
works nicely. However, when I pop it into Cesium, the images are in the
wrong spots and rotated incorrectly. Here's the sandcastle code I used:

```js
var viewer = new Cesium.Viewer("cesiumContainer", {
  skyBox: new Cesium.SkyBox({
    sources : {
      // I have a static server running on localhost
      positiveX : 'http://localhost:4979/Inkedskybox+y.jpg', // rotated 90 to the right
      negativeX : 'http://localhost:4979/Inkedskybox-y.jpg', // rotated 90 to the left
      positiveY : 'http://localhost:4979/Inkedskybox+x.jpg', 
      negativeY : 'http://localhost:4979/Inkedskybox-x.jpg', // rotated 180
      positiveZ : 'http://localhost:4979/Inkedskybox-z.jpg',
      negativeZ : 'http://localhost:4979/Inkedskybox+z.jpg' // rotated 180
    }
  })
});
```

I'll need to look carefully at the axes, both in Cesium and in my code.
I may have the y coordinates flipped. I also might have axes oriented
incorrectly with respect to Cesium's skybox axes. 

## 2021-05-11 Right Way Up

I looked up how WebGL handles cubemap orientation, and was surprised to find
out that A. it's a _left-handed_ coordinate system and B. The UV coordinates
go across the _inside_ of the box (which in retrospect makes sense).

I played around with the UV directions and fixed the `atan2` to handle the
left-handed coordinate system. Now it produces cubemaps I can pop into CesiumJS!

Next Steps:

1. Clean up and document the code better
2. Make some test data to include with the repo
3. Make a standalone CesiumJS page to view the results.
4. Make a README including example output
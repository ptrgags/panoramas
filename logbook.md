# Panorama to Cubemap Logbook

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

## 2021-05-16 Cleanup

Today I did a cleanup pass on the code. I documented the functions in the code
and started to put together a readme.

...I realized I might havve a bug in my code. It seems that `+z` and `-z` are
swapped. This is likely because when testing I had temporarily swapped these
images. I'll have to investigate this further.

Next Steps:
- Double-check my coordinate axes.
- Make a standalone CesiumJS page to view the results
- Finish README

## 2021-05-25 Added a Viewer

Today I added an HTML page that sets up a CesiumJS viewer to display the
output cubemap as a skybox.

Next Steps:
- Sort out the coordinate axes. It might be helpful to make a template image to
help determine which way is up.
- Finish README

## 2021-06-02 New Approach

This past week, I've been thinking about how to generalize this panorama
code. I took inspiration from the [models of the hyperbolic plane](https://en.wikipedia.org/wiki/Hyperbolic_geometry#Connection_between_the_models):

* The equirectangular image represents an entire sphere, (2 hemisphere models)
* The Poincaré disk is the stereographic projection of this hemisphere from -1z
* The hyperboloid model is a different form of stereographic projection from -1z
* The half-plane model is a stereographic projection from -1x
* The Beltrami-Klein disk is an orthographic projection of the hemisphere
* The cubemap is 6 gnomonic projections from the origin

Another thing is you could always rotate the sphere before projecting. This
will likely be more flexible than picking the projection points.

There's more to say on this, but I'm short on time today.

So far I've split the main projection code into classes for an ImagePlane
as well as a UnitSphere. 

One thing I realized: I might have a mistake in how I interpret the
equirectangular map: My longitude increases CCW, but the image from a
panorama is really the _inside_ of the cube, not the outside. This would mean
longitude should increase _clockwise_ - this may be why some of my texture
orientations seem weird (compounded by the WebGL and CesiumJS conventions).
I really need to study this more until I understand which way is up.

## 2021-06-04 Projecting the Other Way

When I made the `UnitSphere` and `ImagePlane` classes the other day, I had
included the inverse functions as well, but I hadn't tested that. So I decided
to add the reverse projection too. Got it producing an image, but two issues
here:

1. It's backwards! probably another "panorama is CW" issue.
2. Projecting the sphere covers the _whole_ image, not just a single plane. This
    ends up projecting the plane twice, once upside down.

I think I need a dedicated `CubeMap` class that internally stores 6
`ImagePlane`s. It should have the same interface as the other classes, but
delegates to the appropriate image plane as needed. This class could also
handle the orientation issues I was having. The one downside is I'll need to
rethink the projection functions since there's 6 targets here, not just 1.
That said, multiple targets will be common. E.g. Poincaré disk needs two maps,
hyperbolic also 2 maps, etc.

Next Steps:

* Continue to investigate the orientation issues
* Design a `CubeMap` class

## 2021-06-08 Added a Cubemap Class

Today I added a `Cubemap` class to make it easier to put together a cubemap.
This handles the 6 faces, so you can think of it as one big cubemap texture.
The inverse projection will be trickier to implement, so I'm going to defer
that until I have a use case.

Along the way, I also made sure the coordinate systems were consistent
in context. Since the equirectangular image uses a left-handed coordinate
system (since it's the inside of the sphere), by the end, the UV directions
were consistent with the OpenGL conventions, and also consistent with
Cesium. I guess I just had a bug in my equirectangular code.

## 2021-06-06 Start Adding Stereographic

Today I added a `StereographicProjection` class which holds two image
planes: one for the northern hemisphere, one for the southern hemisphere.
I also updated the CLI to support more images and input/output formats.

One neat thing is I learned that the projection is almost the same, except
for the sign of z in the denominator, so absolute value can be used to
roll 2 projections into 1!

```
(x, y, z) -> (a, b, 0)

Northern Hemisphere: (z positive)
a = x / (1 + z)
b = y / (1 + z)

Southern Hemisphere: (z negative)
a = x / (1 - z)
b = y / (1 - z)

In general:
a = x / (1 + |z|)
b = y / (1 + |z|)
```

The tricky thing is to handle the projection since we have 2 input images,
and `cv2.remap()` doesn't handle more than one image. So I need to produce
several images and combine them. Fortunately that's easy for stereographic
projection, as there are only 2 images, and they are identified by the
sign of the `z` coordinate on the unit sphere in world space.

However, I'm running into some NumPy errors, and I'm only getting a single line of pixels in the output image. I need to check my calculations
and see if I need to do any special `Inf`/`NaN` handling.

Next steps:
* Debug why I'm not getting a full image
* Update the README with new usage instructions.
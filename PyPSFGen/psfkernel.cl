
// BesselJ1 Function
inline float BesselJ1(float x)
{
    float y = (x < 0.0f) ? -x : x;

    if (y < 3.945f)
    {
        float x2  =  x   * x;
        float x3  =  x2  * x;
        float x5  =  x3  * x2;
        float x7  =  x5  * x2;
        float x9  =  x7  * x2;
        float x11 =  x9  * x2;
        float x13 =  x11 * x2;
        
        return x/2.0f 
             - x3/16.0f 
             + x5/384.0f 
             - x7/18432.0f 
             + x9/1.47456e6f 
             - x11/1.769472e8f 
             + x13/2.97271296e10f;
    } 
    else 
    {
        float y2 = y  * y;
        float y3 = y2 * y;
        float y4 = y2 * y2;

        float answer = native_sqrt(2.0f / (M_PI * y))
                     * (1.0f + 3.0f / (16.0f * y2) - 99.0f / (512.0f * y4))
                     * native_cos(y - 3.0f * M_PI / 4.0f + 3.0f / (8.0f * y) - 21.0f / (128.0f * y3));

        if (x < 0.0f)
            answer = -answer;
        return answer;
    }
}

kernel void pixelPSF(
        const float k, 
        const float a,
        const float dx,
        const int W, 
        const int H,
        const int F,
        __global const int *ptr,
        __global const int *len,
        __global const float *px, 
        __global const float *py,
        __global const float *N, 
        __global const float *width,
        __global float *image)
{
    // get pixel coordinates
    int img = get_global_id(0);
    int m = get_global_id(1);
    int n = get_global_id(2);

    // calculate the exact pixel coordinates
    float xp = (a + dx) * (float) m;
    float yp = (a + dx) * (float) n;

    float Gsum = 0.0f;

    for (int i = 0; i < F; i++) {
    
        float xs = a * (float) i / (float) F + dx*0.5f + a * 0.5f / (float) F;
        float x = xp + xs;

        for (int j = 0; j < F; j++) {

            float ys = a * (float) j / (float) F + dx*0.5f + a * 0.5f / (float) F;
            float y = yp + ys;

            // for all particles
            for (int p = ptr[img]; p < ptr[img] + len[img]; p++)
            {
                float numphoton = (float) N[p];
                float xtemp = (x - px[p]);
                float ytemp = (y - py[p]);
                float r = native_sqrt(xtemp * xtemp + ytemp * ytemp);

                if (r * r < 0.000001f) {
                    r = 0.000001f;
                }
                
                float width1 = width[p] / 1.8666f;

                // "normalize" (I_0 is peak intensity in the Airy-disk)
                float intensity = 975.414f * k * k / (width1 * width1);

                float value = (2.0f * BesselJ1(k * r / width1) * width1 / (k * r));
                Gsum += value * intensity * numphoton * value ;
            }
        }
    }

    // store the average of all samples
    image[m + n * W + img * W * H] = Gsum / (float) (F * F);
}

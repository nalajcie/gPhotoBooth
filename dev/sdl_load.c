/* SDL_image IMG_Load test program
 * compile using:
 *      gcc sdl_load.c -o sdl_load -lSDL -lSDL_image
 */
#include <SDL/SDL.h>
#include <SDL/SDL_image.h>
#include <stdio.h>
#include <time.h>

int main(void)
{

    SDL_Surface* image = NULL;
    SDL_Surface* screen = NULL;

    SDL_Init(SDL_INIT_EVERYTHING);

    /*
    const SDL_VideoInfo* videoInfo = SDL_GetVideoInfo();
    screen = SDL_SetVideoMode(videoInfo->current_w, videoInfo->current_h, videoInfo->vfmt->BitsPerPixel, SDL_SWSURFACE);
    screen = (SDL_SetVideoMode(320,240,32,SDL_SWSURFACE));
    */
    struct timespec t1, t2;
    clock_gettime(CLOCK_MONOTONIC_RAW, &t1);
    SDL_RWops *rwop = SDL_RWFromFile("dummy-preview.jpg","rb");
    image = IMG_LoadJPG_RW(rwop);
    clock_gettime(CLOCK_MONOTONIC_RAW, &t2);
    if (image == NULL) {
        printf("image is null\n");
        return -1;
    }
    uint64_t diff = (t2.tv_sec - t1.tv_sec) * 1000000000 + (t2.tv_nsec - t1.tv_nsec);
    printf("FILE LOAD TIME: %ju nanosecs = %ju.%03ju s\n", diff, diff/1000000000, diff/1000000);

    /*
    SDL_BlitSurface(image,NULL,screen,NULL);

    SDL_Flip(screen);

    SDL_FreeSurface(image);

    SDL_Delay(5000);
    */
    SDL_Quit();
    return 0;
}

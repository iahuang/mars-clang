#define RED 0x00ff0000
#define GREEN 0x0000ff00
#define BLUE 0x000000ff
#define YELLOW 0x00ffff00
#define MAGENTA 0x00ff00ff
#define WHITE 0x00ffffff
#define BLACK 0x00000000

#define BITMAP_PTR (int*)0x010008000

int __SCREEN_WIDTH = 64;

void init_bitmap_display(int screen_width) {
    __SCREEN_WIDTH = screen_width;
}

void draw_pixel(int x, int y, int color) {
    int *dest = BITMAP_PTR + x + y*__SCREEN_WIDTH;
    *dest = color;
}
#define _GNU_SOURCE
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <dlfcn.h>
char *fgets(char *s, int n, FILE *stream) {
    static char *(*real_fgets)(char *, int, FILE *);
    if (!real_fgets) real_fgets=dlsym(RTLD_NEXT,"fgets");
    char *r=real_fgets(s,n,stream);
    long key; int mod,down;
    if (r && sscanf(s,";hostkey %ld %d %d",&key,&mod,&down)==3) {
        void (*event)(long,int)=dlsym(RTLD_DEFAULT,down?"keyboard_key_pressed":"keyboard_key_released");
        if (!event) { fputs("HOSTKEY missing API\n",stderr); abort(); }
        event(key,mod);
        fprintf(stderr,"HOSTKEY %ld %d %d\n",key,mod,down);
        strcpy(s,"\n");
    }
    return r;
}

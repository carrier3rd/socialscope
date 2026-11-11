// badpage_hold (Nov 11 2026): userspace stand-in for BadRAM while the laptop's RAM is faulty and memtest/memmap
// (root) aren't available. Allocates MB megabytes, runs PASSES pattern passes, then mlock()s every 4 KB page that
// showed a bit flip (so the kernel can't give that physical frame to the page cache or another process), munmaps the
// good pages, writes the count to stdout, and sleeps until killed. Only covers frames that were free when it ran.
// RLIMIT_MEMLOCK (8 MB here) caps it at 2048 held pages.
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <unistd.h>
#include <sys/mman.h>
#define PG 4096UL
static uint64_t mix(uint64_t x){x^=x>>33;x*=0xff51afd7ed558ccdULL;x^=x>>33;x*=0xc4ceb9fe1a85ec53ULL;x^=x>>33;return x;}
int main(int argc,char**argv){
  size_t mb=argc>1?strtoul(argv[1],0,10):4096; int passes=argc>2?atoi(argv[2]):6;
  size_t bytes=mb<<20, n=bytes/8, npg=bytes/PG;
  uint64_t*a=mmap(0,bytes,PROT_READ|PROT_WRITE,MAP_PRIVATE|MAP_ANONYMOUS|MAP_POPULATE,-1,0);
  if(a==MAP_FAILED){perror("mmap");return 2;}
  unsigned char*bad=calloc(npg,1); long nbad=0;
  for(int p=0;p<passes;p++){
    uint64_t s=0x9e3779b97f4a7c15ULL*(p+7);
    for(size_t i=0;i<n;i++) a[i]=(p&1)?~mix(i^s):mix(i^s);
    for(size_t i=0;i<n;i++){ uint64_t e=(p&1)?~mix(i^s):mix(i^s); if(a[i]!=e && !bad[i*8/PG]){bad[i*8/PG]=1;nbad++;} }
    fprintf(stderr,"pass %d: %ld bad pages so far\n",p+1,nbad);
  }
  long held=0;
  for(size_t g=0;g<npg;g++){
    char*pg=(char*)a+g*PG;
    if(bad[g]){ if(mlock(pg,PG)==0) held++; else perror("mlock"); }
    else munmap(pg,PG);
  }
  printf("holding %ld of %ld bad pages (tested %zu MB, %d passes)\n",held,nbad,mb,passes); fflush(stdout);
  for(;;) pause();
}

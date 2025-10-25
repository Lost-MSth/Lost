__int64 __fastcall main(int a1, char **a2, char **a3)
{
  size_t v3; // rax
  _BOOL4 v4; // ebx
  const char *v5; // rdi

  puts("Enter your flag:");
  fflush(stdout);
  if ( fgets(byte_4060, 256, stdin) )
  {
    v3 = strlen(byte_4060);
    if ( v3 && byte_4060[v3 - 1] == 10 )
      byte_4060[v3 - 1] = 0;
    __rdtsc();
    __rdtsc();
    v4 = sub_1D80();
    v5 = "Correct!";
    if ( !sub_17E0() && !v4 )
      v5 = "Incorrect!";
    puts(v5);
  }
  return 0LL;
}
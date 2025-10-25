_BOOL8 sub_1D80()
{
  size_t v0; // rdi
  char v1; // cl
  unsigned __int64 i; // rsi
  char v4[120]; // [rsp+0h] [rbp-8B8h] BYREF
  char s1[1024]; // [rsp+78h] [rbp-840h] BYREF
  char s2[1032]; // [rsp+478h] [rbp-440h] BYREF
  unsigned __int64 v7; // [rsp+888h] [rbp-30h]

  v7 = __readfsqword(0x28u);
  __rdtsc();
  v0 = strlen(byte_4030);
  v1 = -76;
  for ( i = 0LL; ; v1 = byte_21A0[i] )
  {
    v4[i] = __ROL1__(v1 ^ byte_4030[i % v0] ^ 0x3C, (i & 3) + 1) ^ 0xA5;
    if ( ++i == 45 )
      break;
  }
  v4[45] = 0;
  sub_1CA0(v4, (__int64)s1);
  sub_1CA0(byte_4060, (__int64)s2);
  return strcmp(s1, s2) == 0;
}
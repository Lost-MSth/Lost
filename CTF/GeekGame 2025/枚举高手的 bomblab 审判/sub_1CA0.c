__int64 __fastcall sub_1CA0(const char *a1, __int64 a2)
{
  size_t v4; // r13
  size_t v5; // r8
  __int64 result; // rax
  __int64 v7; // rdi
  unsigned __int64 v8; // rsi
  unsigned __int8 v9; // dl

  v4 = strlen(a1);
  v5 = strlen(byte_4030);
  __rdtsc();
  result = 0LL;
  if ( v4 )
  {
    v7 = 2LL;
    v8 = 0LL;
    while ( 1 )
    {
      v9 = __ROL1__(a1[v8] ^ byte_4030[v8 % v5], (v8 & 3) + 1);
      result = (unsigned __int8)a0123456789abcd[v9 & 0xF];
      *(_BYTE *)(a2 + 2 * v8) = a0123456789abcd[v9 >> 4];
      *(_BYTE *)(a2 + v7 - 1) = result;
      if ( v4 == ++v8 )
        break;
      v7 += 2LL;
      if ( v8 == 511 )
      {
        v7 = 1022LL;
        break;
      }
    }
  }
  else
  {
    v7 = 0LL;
  }
  *(_BYTE *)(a2 + v7) = 0;
  return result;
}
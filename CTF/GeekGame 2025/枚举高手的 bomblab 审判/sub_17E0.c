// positive sp value has been detected, the output may be wrong!
_BOOL8 sub_17E0()
{
  size_t v0; // rbx
  _BOOL8 result; // rax
  int v2; // r9d
  unsigned __int64 v3; // r8
  unsigned __int8 v4; // dl
  unsigned __int64 v5; // rcx
  int v6; // r10d
  __int64 v7; // rax
  int v8; // edx
  int v9; // r8d
  int v10; // ebx
  __int64 v11; // r11
  __int64 v12; // r9
  _BYTE *v13; // r11
  _BYTE *v14; // rax
  char v15; // r12
  unsigned __int8 v16; // r9
  int v17; // r11d
  char v18; // r12
  char *v19; // r13
  char v20; // cl
  char *v21; // r10
  unsigned __int8 v22; // cl
  __int64 v23; // r13
  __int64 v24; // r10
  int v25; // eax
  unsigned __int64 v26; // rax
  __int64 v27; // rax
  __int64 v28; // rdx
  unsigned __int64 v29; // rax
  int v30; // eax
  int v31; // edx
  int v32; // ebx
  __int64 v33; // rax
  unsigned int v34; // r11d
  int v35; // r12d
  _BYTE *v36; // r9
  __int64 i; // rax
  __int64 v38; // r8
  int v39; // r10d
  int v40; // r13d
  _BYTE *v41; // rax
  _BYTE *v42; // [rsp-880h] [rbp-48B0h]
  unsigned __int8 *v43; // [rsp-878h] [rbp-48A8h]
  unsigned __int64 v44; // [rsp-870h] [rbp-48A0h]
  char v45; // [rsp-865h] [rbp-4895h]
  int v46; // [rsp-864h] [rbp-4894h]
  _DWORD v47[530]; // [rsp-858h] [rbp-4888h] BYREF
  _BYTE v48[16]; // [rsp-10h] [rbp-4040h] BYREF
  __int64 v49; // [rsp+8h] [rbp-4028h] BYREF
  _BYTE v50[11]; // [rsp+1EFh] [rbp-3E41h] BYREF
  _BYTE v51[39]; // [rsp+5F0h] [rbp-3A40h] BYREF
  __int64 v52; // [rsp+9E8h] [rbp-3648h] BYREF
  _QWORD v53[1541]; // [rsp+1008h] [rbp-3028h] BYREF

  while ( &v49 != &v53[-2048] )
    ;
  v53[1534] = __readfsqword(0x28u);
  v0 = strlen(byte_4060);
  result = 0LL;
  if ( v0 == 39 )
  {
    memset(v48, 0, 0x4000uLL);
    qmemcpy(v50, "\nsneaky_key", sizeof(v50));
    qmemcpy(v51, byte_4060, sizeof(v51));
    memset(&v47[2], 0, 0x838uLL);
    __rdtsc();
    v2 = 0;
    v3 = 0LL;
    while ( 1 )
    {
      v4 = *((_BYTE *)&unk_2100 + v3);
      v5 = v3 + 1;
      if ( v4 > 0x21u )
      {
        if ( v4 == 64 )
        {
          v32 = v2 - 3;
          v33 = (unsigned int)v47[v2 + 5];
          if ( (unsigned int)(v33 + 256) > 0x4000 )
            return memcmp(&v52, &unk_2160, 0x27uLL) == 0;
          v34 = v47[v2 + 7];
          v35 = v47[v2 + 6];
          if ( v34 + v35 > 0x4000 )
            return memcmp(&v52, &unk_2160, 0x27uLL) == 0;
          v36 = &v48[v33];
          for ( i = 0LL; i != 256; ++i )
            v36[i] = i;
          v38 = 0LL;
          v39 = 0;
          do
          {
            v40 = (unsigned __int8)v36[v38];
            v39 += v40 + *((unsigned __int8 *)&v47[528] + (unsigned int)v38 % v34 + v35);
            v41 = &v36[(unsigned __int8)v39];
            v36[v38++] = *v41;
            *v41 = v40;
          }
          while ( v38 != 256 );
          v3 = v5;
          v2 = v32;
        }
        else
        {
          if ( v4 != 65 )
            return memcmp(&v52, &unk_2160, 0x27uLL) == 0;
          v6 = v2 - 6;
          v7 = (unsigned int)v47[v2 + 4];
          if ( (unsigned int)(v7 + 256) > 0x4000 )
            return memcmp(&v52, &unk_2160, 0x27uLL) == 0;
          v8 = v47[v2 + 7];
          v9 = v47[v2 + 5];
          if ( (unsigned int)(v8 + v9) > 0x4000 )
            return memcmp(&v52, &unk_2160, 0x27uLL) == 0;
          v10 = v47[v2 + 6];
          if ( (unsigned int)(v8 + v10) > 0x4000 )
            return memcmp(&v52, &unk_2160, 0x27uLL) == 0;
          v11 = (unsigned int)v47[v2 + 3];
          if ( (unsigned int)(v11 + 1) > 0x4000 )
            return memcmp(&v52, &unk_2160, 0x27uLL) == 0;
          v12 = (unsigned int)v47[v6 + 8];
          if ( (unsigned int)(v12 + 1) > 0x4000 )
            return memcmp(&v52, &unk_2160, 0x27uLL) == 0;
          v13 = &v48[v11];
          v44 = v5;
          v14 = &v48[v7];
          v15 = *v13;
          v42 = v13;
          v43 = &v48[v12];
          v16 = v48[v12];
          v17 = 0;
          v45 = v15;
          v18 = v15 + 1;
          v46 = v6;
          while ( v8 != v17 )
          {
            v19 = &v14[(unsigned __int8)(v18 + v17)];
            v20 = *v19;
            v16 += *v19;
            v21 = &v14[v16];
            *v19 = *v21;
            *v21 = v20;
            v22 = *v19 + v20;
            v23 = (unsigned int)(v9 + v17);
            v24 = (unsigned int)(v10 + v17++);
            *((_BYTE *)&v47[528] + v24) = *((_BYTE *)&v47[528] + v23) ^ v14[v22];
          }
          *v42 = v8 + v45;
          *v43 = v16;
          v3 = v44;
          v2 = v46;
        }
      }
      else
      {
        if ( !v4 )
          return memcmp(&v52, &unk_2160, 0x27uLL) == 0;
        switch ( v4 )
        {
          case 1u:
            v3 += 2LL;
            v47[v2++ + 8] = *((unsigned __int8 *)&unk_2100 + v5);
            break;
          case 3u:
            v30 = *((unsigned __int8 *)&unk_2100 + v5) | (*((unsigned __int8 *)&unk_2100 + v3 + 3) << 16) | (byte_2102[v3] << 8);
            v31 = byte_2104[v3];
            v3 += 5LL;
            v47[v2++ + 8] = (v31 << 24) | v30;
            break;
          case 4u:
            --v2;
            ++v3;
            break;
          case 5u:
            v47[v2 + 8] = v47[v2 + 7];
            ++v3;
            ++v2;
            break;
          case 0x20u:
            v27 = v2 - 1;
            v28 = v27 + 8;
            v29 = (unsigned int)v47[v27 + 8];
            if ( v29 > 0x3FFF )
              return memcmp(&v52, &unk_2160, 0x27uLL) == 0;
            v47[v28] = *((unsigned __int8 *)&v47[528] + v29);
            ++v3;
            break;
          case 0x21u:
            v25 = v2 - 1;
            v2 -= 2;
            v26 = (unsigned int)v47[v25 + 8];
            if ( v26 > 0x3FFF )
              return memcmp(&v52, &unk_2160, 0x27uLL) == 0;
            *((_BYTE *)&v47[528] + v26) = v47[v2 + 8];
            ++v3;
            break;
          default:
            return memcmp(&v52, &unk_2160, 0x27uLL) == 0;
        }
      }
      if ( v3 > 0x40 )
        return memcmp(&v52, &unk_2160, 0x27uLL) == 0;
    }
  }
  return result;
}
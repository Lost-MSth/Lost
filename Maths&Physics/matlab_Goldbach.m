%{
Goldbach conjecture

2019.12.11
%}
clc;
clear;
close all;
x=input('Please input a positive even(>=6):','s'); %No check input
len=length(x);
if len<=16
    x=uint64(str2double(x));
    half_x=x/2;
    if isprime(x-3)
        fprintf('%.f=3+%.f\n',x,x-3);
        return;
    end
    for i=6:6:half_x
        if isprime(x-i+1) && isprime(i-1)
            fprintf('%.f=%.f+%.f\n',x,i-1,x-i+1);
            break;
        end
        if isprime(x-i-1) && isprime(i+1)
            fprintf('%.f=%.f+%.f\n',x,i+1,x-i-1);
            break;
        end
    end
else
    %Big Number
    %Too slow!
    a=[];
    for i=1:1:len
        a=[str2double(x(i)) a];
    end
    for i=len:-1:1
        if a(i)==0
            len=len-1;
        else
            break;
        end
    end
    i=[3];
    if if_prime(subtraction(a,i))==1
        print(a,i,subtraction(a,i));
        return;
    end
    i=[6];
    global q lenq MM flag;
    flag=1;
    if len<=20
        MM=ceil(uint64(sqrt(str2double(x))))+10000;
    else
        MM=10000000002;
        flag=0;
    end
    q=primes(MM);
    q(1)=[];
    q(1)=[];
    lenq=length(q);
    while length(i)<len || if_bigger(a,i)
        iaa=subtraction(i,[1]);
        ibb=addition(i,1);
        jaa=subtraction(a,iaa);
        jbb=subtraction(a,ibb);
        if if_prime(iaa) && if_prime(jaa)
            print(a,iaa,jaa);
            break;
        end
        if if_prime(ibb) && if_prime(jbb)
            print(a,ibb,jbb);
            break;
        end
        i=addition(i,6);
    end
end

function f=if_bigger(a,b) %if a>=b then f=1
    lena=length(a);
    lenb=length(b);
    for i=lena:-1:1
        if a(i)==0
            lena=lena-1;
        else
            break;
        end
    end
    for i=lenb:-1:1
        if b(i)==0
            lenb=lenb-1;
        else
            break;
        end
    end
    f=1;
    if lena<lenb
        f=0;
    elseif lena==lenb
        for i=lena:-1:1
            if a(i)>b(i)
                break;
            elseif a(i)<b(i)
                f=0;
                break;
            end
        end
    end
end

function c=subtraction(a,b) %c=a-b
%a>=b
    lena=length(a);
    for i=lena:-1:1
        if a(i)==0
            lena=lena-1;
        else
            break;
        end
    end
    a=[a 0];
    b_lena=b;
    for i=length(b)+1:1:length(a)
        b_lena=[b_lena 0];
    end
    c=zeros(1,lena);
    for i=1:1:lena
        if a(i)>=b_lena(i)
            c(i)=a(i)-b_lena(i);
        else
            c(i)=a(i)+10-b_lena(i);
            a(i+1)=a(i+1)-1;
        end
    end
end

function c=addition(a,x) %c=a+x (x is not a big number)
    lena=length(a);
    for i=lena:-1:1
        if a(i)==0
            lena=lena-1;
        else
            break;
        end
    end
    c=zeros(1,lena+1);
    c(1)=x;
    for i=1:1:lena
        c(i)=a(i)+c(i);
        if c(i)>=10
            c(i)=c(i)-10;
            c(i+1)=c(i+1)+1;
        end
    end
    if c(end)==0
        c(end)=[];
    end
end

function f=if_wholedivide(a,b) %a mod b=r  if r=0 then f=1
    lena=length(a);
    lenb=length(b);
    for i=lena:-1:1
        if a(i)==0
            lena=lena-1;
        else
            break;
        end
    end
    for i=lenb:-1:1
        if b(i)==0
            lenb=lenb-1;
        else
            break;
        end
    end
    j=lena-lenb;
    if if_bigger(a,[zeros(1,j),b])==0 && j>=1
        j=j-1;
    end
    while if_bigger(a,[zeros(1,j),b])==1
        a=subtraction(a,[zeros(1,j),b]);
        while j>=1 && if_bigger([zeros(1,j),b],a)
            j=j-1;
        end
    end
    f=1;
    for i=1:1:length(a)
        if a(i)~=0
            f=0;
            break;
        end
    end
end

function f=if_prime(a) %isprime a>=5
    global q lenq MM flag;
    f=1;
    lena=length(a);
    for i=lena:-1:1
        if a(i)==0
            lena=lena-1;
        else
            break;
        end
    end
    if mod(a(1),2)==0
        f=0;
        return;
    end
    s=0;
    for i=1:1:lena
        s=s+a(i);
    end
    if mod(s,3)==0
        f=0;
        return;
    end
    if if_bigger([8],a)
        return;
    end
    for i=1:1:lenq
        tran_q=transform(q(i));
        if if_bigger(tran_q,a)==1
            return;
        end
        if if_wholedivide(a,tran_q)==1
            f=0;
            return;
        end
    end
    if flag==1 return; end
    j=[MM];
    lenj_max=idivide(lena,int16(2),'ceil');
    j_max=[zeros(1,lenj_max) 1];
    while if_bigger(j_max,j)==1
        if if_wholedivide(a,addition(j,1))==1
            f=0;
            return;
        end
        if if_wholedivide(a,subtraction(j,[1]))==1
            f=0;
            return;
        end
        j=addition(j,6);
    end
end

function nothing=print(a,b,c)
    nothing=0;
    lena=length(a);
    lenb=length(b);
    lenc=length(c);
    for i=lena:-1:1
        if a(i)==0
            lena=lena-1;
        else
            break;
        end
    end
    for i=lenb:-1:1
        if b(i)==0
            lenb=lenb-1;
        else
            break;
        end
    end
    for i=lenc:-1:1
        if c(i)==0
            lenc=lenc-1;
        else
            break;
        end
    end
    for i=lena:-1:1
        fprintf('%.f',a(i));
    end
    fprintf('=');
    for i=lenb:-1:1
        fprintf('%.f',b(i));
    end
    fprintf('+');
    for i=lenc:-1:1
        fprintf('%.f',c(i));
    end
    fprintf('\n');
end

function c=transform(x)
    c=[];
    t=num2str(x);
    for i=length(t):-1:1
        c=[c str2double(t(i))];
    end
end
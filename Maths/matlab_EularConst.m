%{
Euler-Mascheroni constant

2020.5.31

����ʽ��
zeta(2)/2-zeta(3)/3+zeta(4)/4-zeta(5)/5+...
%}
clc;
clear;
close all;

flag=0; %0�����Դ�zeta�������� ����ֵ����ǰm�����
n=1000;
m=100;
p=10;
n=input('�����뽻������������:'); %No check input
if flag~=0
    m=input('����������zeta������������:'); %No check input
end
p=input('������������С��λ��:'); %No check input

s=0;
if flag==0
    for i=2:1:n
        s=s+zeta(i)/i*(-1)^i;
    end
else
    for i=2:1:n
        ss=0;
        for j=1:1:m
            ss=ss+1/j^i;
        end
        s=s+ss/i*(-1)^i;
    end
end
st=['C=%1.',num2str(p),'f'];
fprintf(st,s);
%{
Euler-Mascheroni constant

2020.5.31

计算式：
zeta(2)/2-zeta(3)/3+zeta(4)/4-zeta(5)/5+...
%}
clc;
clear;
close all;

flag=0; %0：用自带zeta函数计算 其他值：用前m项计算
n=1000;
m=100;
p=10;
n=input('请输入交错级数计算项数:'); %No check input
if flag~=0
    m=input('请输入黎曼zeta函数计算项数:'); %No check input
end
p=input('请输入输出结果小数位数:'); %No check input

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
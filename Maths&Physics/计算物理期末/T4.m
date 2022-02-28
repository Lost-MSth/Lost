%{
�����⣬��Բ��ƫ΢�ַ������
����Jacobi�������ͻ���Gauss-Seidel���������ɳڷ�
%}
function main
clear;
clc;
close all;
format long;


% ������
xa_func = @(t) 0; % x������߽�����
xb_func = @(t) t .* (1 - t); % x�����ұ߽�����
ya_func = @(t) 0; % y�����±߽�����
yb_func = @(t) 0; % y�����ϱ߽�����
xa = 0; % x������߽�
xb = 1; % x�����ұ߽�
ya = 0; % y�����±߽�
yb = 1; % y�����ϱ߽�
h = 0.01; % �ָ��
tol = 1 * 10^(-8); % ����׼
omega1 = 1.1; % �ɳ�����
omega2 = 1.9; % �ɳ�����


x = xa: h: xb;
y = ya: h: yb;
[X, Y] = meshgrid(x, y);
S = 6 * X .* Y .* (X-1) + 2 * Y.^3; % ϵ������ע��X��Y�Ƿ���
Z = X.^3 .* Y .* (1 - Y); % ������


% Jacobi������
[u, counter] = Jacobi(xa_func, xb_func, ya_func, yb_func, xa, xb, ya, yb, h, 0.1, tol, S);
fprintf('Jacobi����������������%d\n', counter);
figure;
meshc(X, Y, u');
colormap hsv;
title('Jacobi������');
figure;
meshc(X, Y, u'-Z);
colormap hsv;
title('Jacobi���������');


% ����Gauss-Seidel���������ɳڷ�
[u, counter] = GS_Relaxation(xa_func, xb_func, ya_func, yb_func, xa, xb, ya, yb, h, 0.1, tol, omega1, S);
fprintf('1�ɳڷ��ɳ����ӣ�%g\n', omega1);
fprintf('1����Gauss-Seidel���������ɳڷ�����������%d\n', counter);
figure;
meshc(X, Y, u');
colormap hsv;
title('1����Gauss-Seidel���������ɳڷ�');
figure;
meshc(X, Y, u'-Z);
colormap hsv;
title('1����Gauss-Seidel���������ɳڷ����');

[u, counter] = GS_Relaxation(xa_func, xb_func, ya_func, yb_func, xa, xb, ya, yb, h, 0.1, tol, omega2, S);
fprintf('2�ɳڷ��ɳ����ӣ�%g\n', omega2);
fprintf('2����Gauss-Seidel���������ɳڷ�����������%d\n', counter);
figure;
meshc(X, Y, u');
colormap hsv;
title('2����Gauss-Seidel���������ɳڷ�');
figure;
meshc(X, Y, u'-Z);
colormap hsv;
title('2����Gauss-Seidel���������ɳڷ����');



function [u, counter] = Jacobi(xa_func, xb_func, ya_func, yb_func, xa, xb, ya, yb, h, u0, tol, S)
    %{
        Jacobi�������������Բ��ƫ΢�ַ��̣���һ��߽�����
        IN: *_func �߽纯�����
            * �߽緶Χ
            ��*��xa��x������߽磬xb��x�����ұ߽磬ya��y�����±߽磬yb��y�����ϱ߽磩
            h �ָ��
            u0 ȫ�ֳ�ֵ
            tol ��������Ҫ��
            S ϵ������
        OUT: u ��ά�����
             counter ��������
    %}
    x = xa: h: xb;
    y = ya: h: yb;

    u = zeros(length(x), length(y));
    
    % �߽�����
    u(1, 1: end) = xa_func(y);
    u(end, 1: end) = xb_func(y);
    u(1: end, 1) = ya_func(x);
    u(1: end, end) = yb_func(x);
    % ����ֵ
    u_old = u;
    u(2: end-1, 2: end-1) = u0; 
    
    counter = 0;
    while max(max(abs(u - u_old))) >= tol
        u_old = u; 
        u(2: end-1, 2: end-1) = 0.25 * (u(3: end, 2: end-1) + u(1: end-2, 2: end-1) + u(2: end-1, 3: end) + u(2: end-1, 1: end-2) + h^2 * S(2: end-1, 2: end-1));
        counter = counter + 1;
    end
    
  
function [u, counter] = GS_Relaxation(xa_func, xb_func, ya_func, yb_func, xa, xb, ya, yb, h, u0, tol, omega, S)
    %{
        ����Gauss-Seidel���������ɳڷ��������Բ��ƫ΢�ַ��̣���һ��߽�����
        IN: *_func �߽纯�����
            * �߽緶Χ
            ��*��xa��x������߽磬xb��x�����ұ߽磬ya��y�����±߽磬yb��y�����ϱ߽磩
            h �ָ��
            u0 ȫ�ֳ�ֵ
            tol ��������Ҫ��
            omega �ɳ�����
            S ϵ������
        OUT: u ��ά�����
             counter ��������
    %}
    x = xa: h: xb;
    y = ya: h: yb;

    u = zeros(length(x), length(y));
    
    % �߽�����
    u(1, 1: end) = xa_func(y);
    u(end, 1: end) = xb_func(y);
    u(1: end, 1) = ya_func(x);
    u(1: end, end) = yb_func(x);
    % ����ֵ
    u(2: end-1, 2: end-1) = u0; 
    
    counter = 0;
    max_error=1;
    while abs(max_error) >= tol
        counter = counter+1;
        max_error = 0;
        for i = 2: length(x)-1
            for j = 2: length(y)-1
                relx = omega / 4 * (u(i, j+1) + u(i, j-1) + u(i+1, j) + u(i-1, j) + h^2 * S(i, j) - 4 * u(i, j));
                u(i,j) = u(i,j) + relx;
                if abs(relx) > max_error
                    max_error = abs(relx);
                end
            end
        end
    end
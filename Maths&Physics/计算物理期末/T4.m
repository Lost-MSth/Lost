%{
第四题，椭圆型偏微分方程求解
采用Jacobi迭代法和基于Gauss-Seidel迭代法的松弛法
%}
function main
clear;
clc;
close all;
format long;


% 常量表
xa_func = @(t) 0; % x方向左边界条件
xb_func = @(t) t .* (1 - t); % x方向右边界条件
ya_func = @(t) 0; % y方向下边界条件
yb_func = @(t) 0; % y方向上边界条件
xa = 0; % x方向左边界
xb = 1; % x方向右边界
ya = 0; % y方向下边界
yb = 1; % y方向上边界
h = 0.01; % 分割精度
tol = 1 * 10^(-8); % 误差标准
omega1 = 1.1; % 松弛因子
omega2 = 1.9; % 松弛因子


x = xa: h: xb;
y = ya: h: yb;
[X, Y] = meshgrid(x, y);
S = 6 * X .* Y .* (X-1) + 2 * Y.^3; % 系数矩阵，注意X和Y是反的
Z = X.^3 .* Y .* (1 - Y); % 解析解


% Jacobi迭代法
[u, counter] = Jacobi(xa_func, xb_func, ya_func, yb_func, xa, xb, ya, yb, h, 0.1, tol, S);
fprintf('Jacobi迭代法迭代次数：%d\n', counter);
figure;
meshc(X, Y, u');
colormap hsv;
title('Jacobi迭代法');
figure;
meshc(X, Y, u'-Z);
colormap hsv;
title('Jacobi迭代法误差');


% 基于Gauss-Seidel迭代法的松弛法
[u, counter] = GS_Relaxation(xa_func, xb_func, ya_func, yb_func, xa, xb, ya, yb, h, 0.1, tol, omega1, S);
fprintf('1松弛法松弛因子：%g\n', omega1);
fprintf('1基于Gauss-Seidel迭代法的松弛法迭代次数：%d\n', counter);
figure;
meshc(X, Y, u');
colormap hsv;
title('1基于Gauss-Seidel迭代法的松弛法');
figure;
meshc(X, Y, u'-Z);
colormap hsv;
title('1基于Gauss-Seidel迭代法的松弛法误差');

[u, counter] = GS_Relaxation(xa_func, xb_func, ya_func, yb_func, xa, xb, ya, yb, h, 0.1, tol, omega2, S);
fprintf('2松弛法松弛因子：%g\n', omega2);
fprintf('2基于Gauss-Seidel迭代法的松弛法迭代次数：%d\n', counter);
figure;
meshc(X, Y, u');
colormap hsv;
title('2基于Gauss-Seidel迭代法的松弛法');
figure;
meshc(X, Y, u'-Z);
colormap hsv;
title('2基于Gauss-Seidel迭代法的松弛法误差');



function [u, counter] = Jacobi(xa_func, xb_func, ya_func, yb_func, xa, xb, ya, yb, h, u0, tol, S)
    %{
        Jacobi迭代法，求解椭圆型偏微分方程，第一类边界条件
        IN: *_func 边界函数句柄
            * 边界范围
            （*：xa是x方向左边界，xb是x方向右边界，ya是y方向下边界，yb是y方向上边界）
            h 分割精度
            u0 全局初值
            tol 迭代精度要求
            S 系数矩阵
        OUT: u 二维矩阵解
             counter 迭代次数
    %}
    x = xa: h: xb;
    y = ya: h: yb;

    u = zeros(length(x), length(y));
    
    % 边界条件
    u(1, 1: end) = xa_func(y);
    u(end, 1: end) = xb_func(y);
    u(1: end, 1) = ya_func(x);
    u(1: end, end) = yb_func(x);
    % 启动值
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
        基于Gauss-Seidel迭代法的松弛法，求解椭圆型偏微分方程，第一类边界条件
        IN: *_func 边界函数句柄
            * 边界范围
            （*：xa是x方向左边界，xb是x方向右边界，ya是y方向下边界，yb是y方向上边界）
            h 分割精度
            u0 全局初值
            tol 迭代精度要求
            omega 松弛因子
            S 系数矩阵
        OUT: u 二维矩阵解
             counter 迭代次数
    %}
    x = xa: h: xb;
    y = ya: h: yb;

    u = zeros(length(x), length(y));
    
    % 边界条件
    u(1, 1: end) = xa_func(y);
    u(end, 1: end) = xb_func(y);
    u(1: end, 1) = ya_func(x);
    u(1: end, end) = yb_func(x);
    % 启动值
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
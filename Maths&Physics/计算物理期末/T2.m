%{
第二题，常微分方程组
采用四阶Runge-Kutta法
%}
function main
clc;
clear;
close all;
format long;


% 常量表
t0 = 0; % 起始时间
t1 = 350; % 终止时间
N = 10000; % 分割份数
z0 = [0, 0, 0.2, 0.2]; % 初始条件
func = @(t, y) [y(3), y(4), - y(1) - 2 * y(1) * y(2), - y(2) + y(2)^2 - y(1)^2]; % 导函数句柄


% 常微分方程组计算
t = t0: (t1 - t0) / N: t1;
z = runge_kutta_4(func, t, z0);


% 结果作图
x = z(:, 1);
y = z(:, 2);
figure;
plot(x, y);
title('二维运动轨迹图');

px = z(:, 3);
py = z(:, 4);
E_k = 1/2 * (px.^2 + py.^2);
figure;
plot(t, E_k);
title('动能随时间演化图');

E = E_k + 1/2 * (x.^2 + y.^2) + x.^2 .* y - 1/3 * y.^3;
delta_E = E - E(1);
figure;
plot(t, delta_E);
title('能量差值随时间演化图');



function z = runge_kutta_4(f, t, z0)
    %{
        四阶Runge-Kutta法
        IN: f 导函数句柄数组
            t 自变量数组
            z0 初始值
		OUT: z 解矩阵，一列代表一个分量
    %}
    n = length(t); % 维数
    h = t(2) - t(1); % 自变量间隔
    z(1, :) = z0;
    for i = 1:n-1
        k1 = f(t(i), z(i,:));
        k2 = f(t(i) + 0.5 * h, z(i,:) + h * k1 / 2);
        k3 = f(t(i) + 0.5 * h, z(i,:) + h * k2 / 2);
        k4 = f(t(i) + h, z(i,:) + h * k3);
        z(i + 1, :) = z(i, :) + h * (k1 + 2 * k2 + 2 * k3 + k4) / 6;
    end
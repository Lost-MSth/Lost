%{
第五题，Monte Carlo方法求解定积分
均匀抽样、重要抽样
%}
function main
clear;
clc;
close all;
format long;


% 常量表
f = @(t) 4 * t.^3; % 待积分函数句柄
w = @(x) 2 * x; % 重要抽样法权函数句柄
x = @(y) sqrt(y); % 重要抽样法反函数句柄
N = [10, 100, 1000, 10000, 50000]; % 随机数数量取值


% 计算
fprintf('取点数量\t解析解\t均匀抽样\t重要抽样\n');
for i = 1: length(N)
    [a(i), ea(i)] = integrate_monte_carlo_uniform(f, N(i));
    [b(i), eb(i)] = integrate_monte_carlo_important(f, w, x, N(i));
    c(i) = 1;
    
    fprintf('%g\t%f\t%f\t%f\n', N(i), c(i), a(i), b(i));
end
figure;
plot(1:length(N),c-a,'*-',1:length(N),ea,'+-')
legend('均匀抽样法实际偏差','均匀抽样法标准偏差')
title('均匀抽样误差');
figure;
plot(1:length(N),c-b,'*-',1:length(N),eb,'+-')
legend('重要抽样法实际偏差','重要抽样法标准偏差')
title('重要抽样误差');




function [s, sigma] = integrate_monte_carlo_uniform(func, n)
    %{
        Monte Carlo均匀抽样，函数定义域在0~1上
        IN: func 函数句柄
            n 随机值数量
        OUT: s 积分值
    %}
    x = rand(1, n);
    s = sum(func(x)) / n;
    sigma = sqrt(1/n*sum((1./(1+x.^2)).^2)-(1/n*sum(1./(1+x.^2)))^2)/sqrt(n);

function [s, sigma] = integrate_monte_carlo_important(func, func_w, func_x, n)
    %{
        Monte Carlo重要抽样，函数定义域在0~1上
        IN: func 函数句柄
            func_w 权函数句柄
            func_x 反函数句柄
            n 随机值数量
        OUT: s 积分值
    %}
    y = rand(1, n);
    x = func_x(y);
    w = func_w(x);
    ff = func(x) ./ w;
    s = sum(ff) / n;
    sigma = sqrt((1/n*sum(ff.^2)-(1/n*sum(ff))^2)/n);
    


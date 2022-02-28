%{
�����⣬Monte Carlo������ⶨ����
���ȳ�������Ҫ����
%}
function main
clear;
clc;
close all;
format long;


% ������
f = @(t) 4 * t.^3; % �����ֺ������
w = @(x) 2 * x; % ��Ҫ������Ȩ�������
x = @(y) sqrt(y); % ��Ҫ���������������
N = [10, 100, 1000, 10000, 50000]; % ���������ȡֵ


% ����
fprintf('ȡ������\t������\t���ȳ���\t��Ҫ����\n');
for i = 1: length(N)
    [a(i), ea(i)] = integrate_monte_carlo_uniform(f, N(i));
    [b(i), eb(i)] = integrate_monte_carlo_important(f, w, x, N(i));
    c(i) = 1;
    
    fprintf('%g\t%f\t%f\t%f\n', N(i), c(i), a(i), b(i));
end
figure;
plot(1:length(N),c-a,'*-',1:length(N),ea,'+-')
legend('���ȳ�����ʵ��ƫ��','���ȳ�������׼ƫ��')
title('���ȳ������');
figure;
plot(1:length(N),c-b,'*-',1:length(N),eb,'+-')
legend('��Ҫ������ʵ��ƫ��','��Ҫ��������׼ƫ��')
title('��Ҫ�������');




function [s, sigma] = integrate_monte_carlo_uniform(func, n)
    %{
        Monte Carlo���ȳ�����������������0~1��
        IN: func �������
            n ���ֵ����
        OUT: s ����ֵ
    %}
    x = rand(1, n);
    s = sum(func(x)) / n;
    sigma = sqrt(1/n*sum((1./(1+x.^2)).^2)-(1/n*sum(1./(1+x.^2)))^2)/sqrt(n);

function [s, sigma] = integrate_monte_carlo_important(func, func_w, func_x, n)
    %{
        Monte Carlo��Ҫ������������������0~1��
        IN: func �������
            func_w Ȩ�������
            func_x ���������
            n ���ֵ����
        OUT: s ����ֵ
    %}
    y = rand(1, n);
    x = func_x(y);
    w = func_w(x);
    ff = func(x) ./ w;
    s = sum(ff) / n;
    sigma = sqrt((1/n*sum(ff.^2)-(1/n*sum(ff))^2)/n);
    


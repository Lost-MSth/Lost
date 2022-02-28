%{
�ڶ��⣬��΢�ַ�����
�����Ľ�Runge-Kutta��
%}
function main
clc;
clear;
close all;
format long;


% ������
t0 = 0; % ��ʼʱ��
t1 = 350; % ��ֹʱ��
N = 10000; % �ָ����
z0 = [0, 0, 0.2, 0.2]; % ��ʼ����
func = @(t, y) [y(3), y(4), - y(1) - 2 * y(1) * y(2), - y(2) + y(2)^2 - y(1)^2]; % ���������


% ��΢�ַ��������
t = t0: (t1 - t0) / N: t1;
z = runge_kutta_4(func, t, z0);


% �����ͼ
x = z(:, 1);
y = z(:, 2);
figure;
plot(x, y);
title('��ά�˶��켣ͼ');

px = z(:, 3);
py = z(:, 4);
E_k = 1/2 * (px.^2 + py.^2);
figure;
plot(t, E_k);
title('������ʱ���ݻ�ͼ');

E = E_k + 1/2 * (x.^2 + y.^2) + x.^2 .* y - 1/3 * y.^3;
delta_E = E - E(1);
figure;
plot(t, delta_E);
title('������ֵ��ʱ���ݻ�ͼ');



function z = runge_kutta_4(f, t, z0)
    %{
        �Ľ�Runge-Kutta��
        IN: f �������������
            t �Ա�������
            z0 ��ʼֵ
		OUT: z �����һ�д���һ������
    %}
    n = length(t); % ά��
    h = t(2) - t(1); % �Ա������
    z(1, :) = z0;
    for i = 1:n-1
        k1 = f(t(i), z(i,:));
        k2 = f(t(i) + 0.5 * h, z(i,:) + h * k1 / 2);
        k3 = f(t(i) + 0.5 * h, z(i,:) + h * k2 / 2);
        k4 = f(t(i) + h, z(i,:) + h * k3);
        z(i + 1, :) = z(i, :) + h * (k1 + 2 * k2 + 2 * k3 + k4) / 6;
    end
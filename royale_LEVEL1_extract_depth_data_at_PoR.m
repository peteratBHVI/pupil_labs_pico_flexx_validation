function [por_depth_data, world_frame_idx] = royale_LEVEL1_extract_depth_data_at_PoR(...
    FileName, world_data, disp_pointcloud, world_frame_idx)
%ROYALE_LEVEL1_SAMPLE3 - royale example #3:
% 

% % % %  
% """
% (*)~---------------------------------------------------------------------------
% amendments to ROYALE_LEVEL1_SAMPLE3 - royale example #3:
% author: p.wagner@unsw.edu.au / p.wagner@bhvi.org
% 
% find all target positions in point cloud of accuray recording  
%     data output: data talbe with all x y positions of all targets sorted 
% 
% dependencies:
%     - FileName == point cloud in accuracy recording folder 
%     - disp_pointcloud - visualize point cloud (very slow but looks good) 
% ---------------------------------------------------------------------------~(*)
% """
% % %   

% retrieve royale version information
royaleVersion = royale.getVersion();
fprintf('* royale version: %s\n',royaleVersion);

% open recorded file
manager = royale.CameraManager();
cameraDevice = manager.createCamera(FileName);
delete(manager);

cameraDevice.initialize();

% display some information about the connected camera
fprintf('====================================\n');
fprintf('        Camera information\n');
fprintf('====================================\n');
fprintf('Id:              %s\n',cameraDevice.getId());
fprintf('Type:            %s\n',cameraDevice.getCameraName());
fprintf('Width:           %u\n',cameraDevice.getMaxSensorWidth());
fprintf('Height:          %u\n',cameraDevice.getMaxSensorHeight());

% retrieve valid use cases
UseCases=cameraDevice.getUseCases();
fprintf('Use cases: %d\n',numel(UseCases));
fprintf('    %s\n',UseCases{:});
fprintf('====================================\n');

if (numel(UseCases) == 0)
    error('No use case available');
end

% configure playback
cameraDevice.loop(false);
cameraDevice.useTimestamps(false);

N_Frames= cameraDevice.frameCount();
fprintf('Retrieving %d frames...\n',N_Frames);

% start capture mode
cameraDevice.startCapture();

% initialize preview figure
hFig=figure('Name',...
    ['Preview: ',cameraDevice.getId(),' @ MODE_PLAYBACK'],...
    'IntegerHandle','off','NumberTitle','off');
colormap(jet(256));
TID = tic();
last_toc = toc(TID);
iFrame = 0;

% allocate variables 
data_depth_map = zeros(224, 171);
por_depth_data = create_tablle_depth_data(); 
% por_depth_data = array2table(zeros(1,23));

while (ishandle(hFig)) && (iFrame < N_Frames) && ... 
        (world_frame_idx < length(world_data(:,1))) 
    % retrieve data from camera
    data = cameraDevice.getData();
    iFrame = iFrame + 1;
    world_frame_idx = world_frame_idx +1;
    if (mod(iFrame,100) == 0)
        this_toc=toc(TID);
        fprintf('FPS = %.2f\n',100/(this_toc-last_toc));
        fprintf('world_frame_idx = %.0f\n',(world_frame_idx));
        last_toc=this_toc;
    end
    
    %%% notice: figures are slow.
    %%% For higher FPS (e.g. 45), do not display every frame.
    %%% e.g. by doing here:
    % if (mod(iFrame,5) ~= 0);continue;end;
    
    % prepare data, calculate distance for all data points and 
    % limit distance range  
    data_depth_map = sqrt(data.x.^2 + data.y.^2 + data.z.^2);
%     data_depth_map(data_depth_map(:,:) < 0.2) = nan;
    data_depth_map(data_depth_map(:,:) > 4.6) = nan;
    for r = linspace(2,20,10) 
    	[row, col] = data_radi(r, ...
            world_data(world_frame_idx, 6), ...
            world_data(world_frame_idx, 7));
        
        linearidx = sub2ind(size(data_depth_map),row, col);
        por_data = data_depth_map(linearidx);
        por_data(por_data < .14) = nan;
        por_data(por_data > 5) = nan; 
        data.noise(data.noise <0.01) = nan;
        data.depthConfidence(data.depthConfidence <0.01) = nan;
        if ~isempty(por_data)
            new_table = create_tablle_depth_data(); 
            new_table(1 , 'frame_timestamp') = num2cell(world_data(world_frame_idx, 1));
            new_table(1 , 'gaze_ts')         = num2cell(world_data(world_frame_idx, 4));
            new_table(1 , 'frame_idx')       = num2cell(world_frame_idx);
            new_table(1 , 'radius')          = num2cell(r);
            new_table(1 , 'mask_size_pixels')= num2cell(length(row(:,1)));
            new_table(1 , 'total_point_count')= num2cell(length(row(:,1)));
            % valid points == points with depth data 
            new_table(1 , 'valid_point_count')= num2cell(length(por_data(~isnan(por_data))));
           
            new_table(1 , 'point_percentage') = num2cell(new_table.valid_point_count /...
                                                 new_table.total_point_count);
            overexp = data.grayValue(linearidx);
            overexp = overexp(overexp > 65000);
            new_table(1 , 'point_overexposed') = num2cell(length(overexp));
            
            highconfi = data.depthConfidence(linearidx); 
            highconfi = highconfi(highconfi > 25);
            new_table(1 , 'point_confidence') = num2cell(length(highconfi));
            
            
            new_table(1 , 'depth_min') = num2cell(min(por_data));
            new_table(1 , 'depth_mean') = num2cell(nanmean(por_data));
            new_table(1 , 'depth_max') = num2cell(max(por_data));
            new_table(1 , 'depth_stddev') = num2cell(nanstd(por_data));

            new_table(1 , 'noise_min') = num2cell(min(data.noise(linearidx)));
            new_table(1 , 'noise_mean') = num2cell(nanmean(data.noise(linearidx)));
            new_table(1 , 'noise_max') = num2cell(max(data.noise(linearidx)));
            new_table(1 , 'noise_stddev') = num2cell(nanstd(data.noise(linearidx)));
            
            por_confi = data.depthConfidence(linearidx);
            por_confi(por_confi < 1) = nan;
            new_table(1 , 'confidence_min') = num2cell(min(por_confi));
            new_table(1 , 'confidence_mean') =  num2cell(nanmean(por_confi));
            new_table(1 , 'confidence_max') = num2cell(max(por_confi));
%             new_table(1 , 'confidence_stddev') = num2cell(nanstd(por_confi));
            if ~isnan(new_table.depth_mean)
                por_depth_data = [por_depth_data; new_table];
            end
        end
        

        
%       % visualize data on demand     
        if disp_pointcloud && r==4
            data_depth_map(linearidx) = 3;
            set(0,'CurrentFigure',hFig);       
            my_image(data_depth_map,'depth data with found targets');
            drawnow;
        end     
    end
end
world_frame_idx = world_frame_idx - 1; 
% stop capture mode
fprintf('* Stopping capture mode...\n');
cameraDevice.stopCapture();
fprintf('* ...done!\n');
close all
end

function my_image(CData,Name)
% convenience function for faster display refresh:
%  only update 'CData' on successive image calls
%  (does not update title or change resolution!)
if ~isappdata(gca,'my_imagehandle')
    my_imagehandle = imagesc(CData);
    axis image
    title(Name);
    setappdata(gca,'my_imagehandle',my_imagehandle);
else
    my_imagehandle = getappdata(gca,'my_imagehandle');
    set(my_imagehandle,'CData',CData);
end
end


% % % create datatable with sorted target info
function [t3] = create_tablle_depth_data()
% set up output file 
uuii = zeros(1, 24);
colNames = {'frame_timestamp',...
            'gaze_ts', ...
            'frame_idx', ...
            'tag', ... 
            'radius', ... 
            'mask_size_pixels', ...
            'total_point_count', ...
            'valid_point_count', ...
            'point_percentage', ... 
            'point_overexposed', ...
            'point_confidence',...
            'point_missing', ...
            'depth_min', ...
            'depth_mean', ...
            'depth_max', ...
            'depth_stddev', ...
            'noise_min', ...
            'noise_mean', ...
            'noise_max', ...
            'noise_stddev', ...
            'confidence_min', ...
            'confidence_mean', ...
            'confidence_max', ...
            'confidence_stddev'            
            };
        
t3 = array2table(uuii, 'VariableNames', colNames);
end


% % % find each target in each q and sort to target id
function [row, col] = data_radi(r, x, y)
    % calculares row and col idx for data extraction from point
    % cloud 
    por_data_matrix = ones(2*r+1, 2*r+1);
    [row_0, col_0] = find(por_data_matrix);
    for idx = 1:length(row_0)            
        por_data_matrix(row_0(idx), col_0(idx)) = (col_0(idx)-r-1)^2 +(row_0(idx)-r-1)^2;
        if por_data_matrix(row_0(idx), col_0(idx)) > (r^2)
            por_data_matrix(row_0(idx), col_0(idx)) = 0;
        elseif por_data_matrix(row_0(idx), col_0(idx)) == 0
            por_data_matrix(row_0(idx), col_0(idx)) = 1;
        end
    end
    [row, col] = find(por_data_matrix);       
    % adjust coordinates to gaze coordinats 
    row = (row - r -1 +round(y));
    col = (col - r -1 +round(x));
    % eliminate coordinats beyond picoflexx grid 
    for idx = 1:length(row)
        if (row(idx) < 1) || (col(idx) < 1)
            row(idx) = nan;
            col(idx) = nan;
        elseif (row(idx) > 171) || (col(idx) > 224)
            row(idx) = nan;
            col(idx) = nan;            
        end
    end
    row = row(~isnan(row));
    col = col(~isnan(col));
end        

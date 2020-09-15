
% % % %  
% """
% (*)~---------------------------------------------------------------------------
% author: p.wagner@unsw.edu.au / p.wagner@bhvi.org
% 
% extract depth data from point of regard
%   - matching pointcloud and gaze data 
%   - record various radii for analyses  
% 
% dependencies:
%     - royale_LEVEL1_extract_depth_data_at_ PoR(.... )
%     - fp == filepath of recording folder 
%     - disp_pointcloud - visualize point cloud (very slow but looks good) 
% ---------------------------------------------------------------------------~(*)
% """
% % %   

rec_fp = 'D:\PupilLabsRecordings'; 
pxs = string([2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 14]);
accs = ["acc_rec_initial", "acc_rec_5min", "acc_rec_1hour"]; 

fps = get_fps(rec_fp, pxs, accs); 

for idx = 1 : length(fps)
    fps(idx, 3)
    if ~isfile(join([fps(idx, 3), '\gaze_depth_post_hoc.csv'], ''))
        extract_distance_por_from_pointcloud(fps(idx, 3))
        fps(idx, 4) = "completed";
    else 
        fps(idx, 4)= "completed previously";
    end 
end 

% match world timestamps [ts] with closest gaze ts and gaze coordinates 
% fp = 'D:\PupilLabsRecordings\2020_06_04\007';

function extract_distance_por_from_pointcloud(fp) 
    world_TSs = readNPY(join([fp, '\world_timestamps.npy'], ''));

    gazefile = dir(join([fp, '\**\gaze_pos*.csv'], ''))
    [g_data, fileerror] = GetPupilLabCSVData.Gaze([gazefile.folder '\gaze_positions.csv']);
    world_TSs(:,2:4) = nan;
    for idx = 1:length(world_TSs(:,1))
        world_ts = world_TSs(idx,1);
        [delta_t, gaze_idx] = min(abs(g_data(:,1) - world_ts));
        world_TSs(idx, 2) = delta_t;
        world_TSs(idx, 3) = gaze_idx;
        world_TSs(idx, 4) = g_data(gaze_idx, 1);

        world_TSs(idx, 5) = g_data(gaze_idx, 3);
        world_TSs(idx, 6) = g_data(gaze_idx, 4) * 224;
        world_TSs(idx, 7) = g_data(gaze_idx, 5) * 171;   
    end

    world_frame_idx = 0; 
    pc_fp_n = dir(fullfile(fp, 'pointcloud*.rrf'));
    por_depth_data_all = [];
    for idx = 1:size(pc_fp_n,1)

        fp_n = (fullfile(pc_fp_n(idx).folder, pc_fp_n(idx).name));
        disp(fp_n)

        [por_depth_data, world_frame_idx] = royale_LEVEL1_extract_depth_data_at_PoR(fp_n, world_TSs, false, world_frame_idx);
        if por_depth_data.frame_timestamp(1) == 0
            por_depth_data(1,:) = [];
        end
        por_depth_data_all = [por_depth_data_all; por_depth_data];

    end

    writetable(por_depth_data_all, join([fp, '\gaze_depth_post_hoc.csv'], ''));
    if isfile(join([fp, '\gaze_depth_post_hoc.csv'], ''))
        fprintf('* ... file saved!\n');
    else
        fprintf('* ... file not created!\n');
    end
end 


function [fp_data] = get_fps(rec_fp, pxs, accs)
    % Import the data
    [~, ~, px_data] = xlsread('C:\Users\p.wagner\Documents\experiment_execution_logV.2.xlsx','master','A1:Y28');
    px_data = string(px_data);
    px_data(ismissing(px_data)) = '';
    fp_data = [];
    for idx = 1 : length(pxs)
        for idx2 = 1: length(accs)
            fp_data_new(1, 1) = pxs(idx);
            fp_data_new(1, 2) = accs(idx2);
            col = find(px_data(1, :) == pxs(idx));
            row = find(px_data(:,1) == accs(idx2));
            fp_data_new(1, 3) = join([rec_fp, px_data(4, col), px_data(row, col).erase('\')], '\');
            fp_data = [fp_data; fp_data_new ];
        end
    end 
end 
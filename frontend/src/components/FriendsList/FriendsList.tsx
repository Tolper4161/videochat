import type { FriendItemProps } from "./FriendItem";
import FriendItem from "./FriendItem";

import "./FriendsList.css";

interface FriendsListProps {
    data: FriendItemProps[]
}

const FriendsList = ({ data }: FriendsListProps) => {
    return (
        <ul className="friends">
            {
                data.map((friend: FriendItemProps) => (
                    <FriendItem avatar={ friend.avatar } username={ friend.username } />
                ))
            }
        </ul>
    );
};

export default FriendsList;

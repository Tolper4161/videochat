export interface FriendItemProps {
    avatar: string,
    username: string
}

const FriendItem = ({ avatar, username }: FriendItemProps) => {
    return (
        <li className="friend">
            <img
                src={ avatar }
                className="friend__avatar"
            />
            <span className="friend__username">{ username }</span>
        </li>
    );
};

export default FriendItem;
